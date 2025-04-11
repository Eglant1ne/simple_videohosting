package handler

import (
    "encoding/json"
    "net/http"
)

type HealthResponse struct {
    Msg string `json:"msg"`
}

func HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
    response := HealthResponse{Msg: "healthy"}
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(response)
}
