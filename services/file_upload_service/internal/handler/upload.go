package handler

import (
	"fmt"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/internal/service"
)

func fileUploadHandler(s3svc *service.S3Service) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		r.ParseMultipartForm(10 << 20)

		file, handler, err := r.FormFile("file")
		if err != nil {
			http.Error(w, "invalid file", http.StatusBadRequest)
			return
		}
		defer file.Close()

		key := handler.Filename
		if err := s3svc.UploadStream(r.Context(), key, file); err != nil {
			http.Error(w, "upload error", http.StatusInternalServerError)
			return
		}

		fmt.Fprintf(w, "uploaded: %s", key)
	}
}
