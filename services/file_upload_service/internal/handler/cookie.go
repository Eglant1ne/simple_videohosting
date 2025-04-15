package handler

import "net/http"

func getCookieHandler(w http.ResponseWriter, r *http.Request) (string, error) {
	cookie, err := r.Cookie("access_token")
	if err != nil {
		return "", err
	}
	return cookie.Value, nil
}
