FROM ollama/ollama:0.11.8 AS builder

RUN ollama serve & sleep 5 && \
    ollama pull mistral:7b && \
    pkill ollama

FROM ollama/ollama:0.11.8 AS runtime

COPY --from=builder /root/.ollama /root/.ollama
