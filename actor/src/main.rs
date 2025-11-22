#![warn(clippy::unwrap_used, clippy::expect_used)]
use anyhow::bail;
use futures_lite::StreamExt as _;
use lapin::{Connection, ConnectionProperties, options::*, types::FieldTable};
use sentry::{init as sentry_init, types::Dsn};
use serde_json::Value;
use std::path::Path;
use std::process::Command;
use std::str;
use std::{fs, str::FromStr};
use tracing::{Level, event, info, instrument};
use tracing_subscriber::Layer as _;
use tracing_subscriber::layer::SubscriberExt as _;
use tracing_subscriber::util::SubscriberInitExt as _;

fn load_sentry_dsn_from_file(path: &str) -> anyhow::Result<String> {
    let dsn = fs::read_to_string(path)?.trim().to_string();
    if dsn.is_empty() {
        anyhow::bail!("Sentry DSN file is empty");
    }
    Ok(dsn)
}

#[derive(argh::FromArgs)]
/// React to events happening in a rabbitmq queue
struct Cmd {
    /// URL to the Rabbit MQ broker
    #[argh(option, default = "String::from(\"amqp://127.0.0.1:5672\")")]
    rmq_addr: String,

    /// path of the scripts that will be executed
    #[argh(option)]
    script_dir: Option<std::path::PathBuf>,
}

fn main() -> anyhow::Result<()> {
    let stdout_layer = tracing_subscriber::fmt::layer().with_filter(
        tracing_subscriber::EnvFilter::builder()
            .with_default_directive(tracing::level_filters::LevelFilter::INFO.into())
            .from_env_lossy(),
    );
    let sentry_layer = sentry::integrations::tracing::layer()
        .event_filter(|md| match *md.level() {
            tracing::Level::ERROR => sentry_tracing::EventFilter::Event,
            _ => sentry_tracing::EventFilter::Ignore,
        })
        .span_filter(|md| matches!(*md.level(), tracing::Level::ERROR | tracing::Level::WARN));

    tracing_subscriber::registry()
        .with(stdout_layer)
        .with(sentry_layer)
        .init();

    let sentry_dsn = load_sentry_dsn_from_file("sentry_dsn.txt")
        .ok()
        .and_then(|v| {
            Dsn::from_str(&v)
                .map_err(|e| {
                    tracing::event!(
                        tracing::Level::ERROR,
                        error = e.to_string(),
                        "loading sentry dsn"
                    );
                })
                .ok()
        });

    let _sentry_guard = sentry_init(sentry::ClientOptions {
        release: sentry::release_name!(),
        dsn: sentry_dsn,
        ..Default::default()
    });

    let cmd: Cmd = argh::from_env();

    let script_dir = cmd
        .script_dir
        .unwrap_or(std::env::current_dir()?)
        .canonicalize()?;

    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(async_main(&cmd.rmq_addr, &script_dir))?;

    Ok(())
}

async fn async_main(rabbitmq_addr: &str, script_dir: &Path) -> anyhow::Result<()> {
    info!("Starting RabbitMQ consumer...");

    let connection = Connection::connect(rabbitmq_addr, ConnectionProperties::default()).await?;
    let channel = connection.create_channel().await?;

    let exchange_name = "jeeves";
    channel
        .exchange_declare(
            exchange_name,
            lapin::ExchangeKind::Direct,
            ExchangeDeclareOptions::default(),
            FieldTable::default(),
        )
        .await?;

    let queue_name = "webhooks";
    channel
        .queue_declare(
            queue_name,
            QueueDeclareOptions::default(),
            FieldTable::default(),
        )
        .await?;

    channel
        .queue_bind(
            queue_name,
            exchange_name,
            queue_name,
            QueueBindOptions::default(),
            FieldTable::default(),
        )
        .await?;

    let mut consumer = channel
        .basic_consume(
            queue_name,
            "actor",
            BasicConsumeOptions {
                exclusive: true,
                ..Default::default()
            },
            FieldTable::default(),
        )
        .await?;

    let my_span = tracing::error_span!("rmq_loop", queue_name = queue_name.to_string());
    let _span_guard = my_span.enter();
    while let Some(delivery) = consumer.next().await {
        let delivery = delivery?;
        let body = str::from_utf8(&delivery.data)?;
        let project = match get_project_from_message(body).await {
            Ok(project) => {
                info!("handled");
                delivery.ack(BasicAckOptions::default()).await?;
                project
            }
            Err(e) => {
                event!(Level::ERROR, "parsing message {e}");
                delivery
                    .nack(BasicNackOptions {
                        multiple: false,
                        requeue: false,
                    })
                    .await?;
                continue;
            }
        };
        if let Err(e) = run_script(script_dir, &project) {
            event!(Level::ERROR, "running script {e}");
            delivery
                .nack(BasicNackOptions {
                    multiple: false,
                    requeue: false,
                })
                .await?;
            continue;
        }
    }

    Ok(())
}

#[instrument]
async fn get_project_from_message(body: &str) -> anyhow::Result<String> {
    info!("Processing message: {}", body);
    let data: Value = serde_json::from_str(body)?;
    let project = data
        .get("project")
        .and_then(|v| v.as_str())
        .ok_or(anyhow::anyhow!("No 'project' tag found in the message."))?;

    info!("Received project: {}", project);
    Ok(project.to_string())
}

#[instrument]
fn run_script(directory: &Path, script: &str) -> anyhow::Result<()> {
    info!(
        "Running script '{}' in directory '{}'",
        script,
        directory.display()
    );

    let full_path = directory.join(script);
    if !matches!(full_path.parent(), Some(p) if p == directory) {
        bail!("Script had some relative path {}", script);
    }
    info!("{}", full_path.display());
    let output = Command::new(full_path).current_dir(directory).output()?;

    if !output.status.success() {
        let error = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("Command failed: {}", error);
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    info!("Command output: {}", stdout);

    Ok(())
}
