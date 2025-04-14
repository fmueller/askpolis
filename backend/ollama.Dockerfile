FROM ollama/ollama:0.6.5 AS builder

RUN ollama serve & sleep 5 && \
    ollama pull llama3.1 && \
    ollama pull llama3.2 && \
    pkill ollama

FROM ollama/ollama:0.6.5 AS runtime

COPY --from=builder /root/.ollama /root/.ollama
