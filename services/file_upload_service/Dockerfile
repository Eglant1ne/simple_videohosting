FROM golang:1.22.0-alpine AS builder

RUN apk add --no-cache git

WORKDIR /file_upload_service

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN go build -o file-upload ./cmd/server

FROM alpine:latest

WORKDIR /root/

RUN apk --no-cache add ca-certificates

COPY --from=builder /app/file-upload .

COPY .env .

EXPOSE 8080

CMD ["./file-upload"]
