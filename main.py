import logging
import os

import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session

from database import engine, get_db
from models import LogEntry
from schemas import LogCreate, LogResponse

load_dotenv()

# Cria um logger dedicado para a aplicação
logger = logging.getLogger("logguardian")

LogEntry.metadata.create_all(bind=engine)

app = FastAPI(
    title="LogGuardian API",
    description="API de Centralização de Logs e Alerta de Erros em Tempo Real",
    version="1.0.0",
)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


def send_discord_alert(service: str, level: str, message: str) -> None:
    if not DISCORD_WEBHOOK_URL:
        return

    payload = {
        "content": (
            f"🚨 **ALERTA DE LOG CRÍTICO** 🚨\n"
            f"**Serviço:** `{service}`\n"
            f"**Nível:** `{level}`\n"
            f"**Mensagem:** ```{message}```"
        )
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except requests.RequestException as e:
        logger.error("Erro ao enviar alerta para o Discord: %s", e)


@app.post("/logs", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
def receive_log(
    log: LogCreate,
    db: Session = Depends(get_db),  # noqa: B008
) -> LogEntry:
    # 1. Salva o log no SQLite
    db_log = LogEntry(
        service_name=log.service_name,
        level=log.level.upper(),
        message=log.message,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    # 2. Analisa a severidade e dispara alerta imediato se for erro ou crítico
    if log.level.upper() in ["ERROR", "CRITICAL"]:
        send_discord_alert(log.service_name, log.level, log.message)

    return db_log


@app.get("/logs", status_code=status.HTTP_200_OK)
def list_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),  # noqa: B008
) -> list[LogEntry]:
    logs = db.query(LogEntry).offset(skip).limit(limit).all()
    return logs
