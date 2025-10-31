FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    build-essential \
    golang-go \
    git \
    ffmpeg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /video_postprocess
ENV GOPATH=/go
ENV PATH=$PATH:/usr/lib/go/bin:$GOPATH/bin

COPY . .

RUN rm -f go.mod
RUN rm -f go.sum
RUN go mod init github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service
RUN go mod tidy
RUN go build ./cmd/server/

EXPOSE 8090

CMD ["./server"]