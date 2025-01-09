FROM ollama/ollama:0.5.4 AS builder

RUN ollama serve & sleep 5 && \
    ollama pull llama3.1 && \
    ollama pull llama3.2 && \
    pkill ollama

FROM ollama/ollama:0.5.4 AS runtime

COPY --from=builder /root/.ollama /root/.ollama
