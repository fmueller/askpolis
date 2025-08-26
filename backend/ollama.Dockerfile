FROM ollama/ollama:0.11.7 AS builder

RUN ollama serve & sleep 5 && \
    ollama pull mistral:7b && \
    pkill ollama

FROM ollama/ollama:0.11.7 AS runtime

COPY --from=builder /root/.ollama /root/.ollama
