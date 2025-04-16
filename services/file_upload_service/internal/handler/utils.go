package handler

import (
	"encoding/json"
	"net/http"
)

type JsonResponse struct {
	Status  int    `json:"status"`
	Message string `json:"message"`
}

func JSONResponse(w http.ResponseWriter, statusCode int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	response := JsonResponse{
		Status:  statusCode,
		Message: message,
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "Failed to encode JSON response", http.StatusInternalServerError)
	}
}

func RespondError(w http.ResponseWriter, code int, message string) {
	JSONResponse(w, code, message)
}
