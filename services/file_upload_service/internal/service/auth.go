package service

import (
	"bytes"
	"encoding/json"
	"net/http"
	"time"
)

type User struct {
	ID         int     `json:"id"`
	Username   string  `json:"username"`
	Email      string  `json:"email"`
	CreatedAt  string  `json:"created_at"`
	AvatarPath *string `json:"avatar_path"`
}

type AuthResponse struct {
	Msg  string `json:"msg"`
	User User   `json:"user"`
}

var httpClient = &http.Client{
	Timeout: 3 * time.Second,
}

func IsAuthenticated(token string) (AuthResponse, int) {
	url := "http://auth_service:8000/auth/token"

	requestBody := map[string]string{
		"token": token,
	}
	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return AuthResponse{Msg: "Неверные данные запроса"}, http.StatusBadRequest
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return AuthResponse{Msg: "Не удалось создать запрос"}, http.StatusBadRequest
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := httpClient.Do(req)
	if err != nil {
		return AuthResponse{Msg: "Служба аутентификации недоступна"}, http.StatusBadGateway
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return AuthResponse{Msg: "Не авторизованный пользователь"}, resp.StatusCode
	}

	var authResp AuthResponse
	if err := json.NewDecoder(resp.Body).Decode(&authResp); err != nil {
		return AuthResponse{Msg: "Не удалось проанализировать ответ"}, http.StatusInternalServerError
	}

	return authResp, http.StatusOK
}
