package api

import (
	"bytes"
	"encoding/json"
	"net/http"
)

func IsAuthenticated(token string) int {
	url := "http://auth_service:8000/auth/token"

	requestBody := map[string]string{
		"token": token,
	}

	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return http.StatusBadRequest
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return http.StatusBadRequest
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return http.StatusBadGateway
	}

	return resp.StatusCode
}
