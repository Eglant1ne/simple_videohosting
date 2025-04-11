FROM ubuntu:24.10

RUN apt-get update && apt-get install -y \
    build-essential \
    golang-go \
    git \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /file_upload
ENV GOPATH=/go
ENV PATH=$PATH:/usr/lib/go/bin:$GOPATH/bin

COPY . .

RUN go mod init github.com/Eglant1ne/simple_videohosting/services/file_upload_service
RUN go mod tidy
RUN go build ./cmd/server/

EXPOSE 8080

CMD ["./server"]