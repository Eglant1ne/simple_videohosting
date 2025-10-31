package service

import (
	"bytes"
	"io"
	"net/http"
	"path/filepath"
	"strings"
)

func IsVideoFile(part io.Reader, filename string) (io.Reader, bool, error) {
	buffer := make([]byte, 512)
	n, err := part.Read(buffer)
	if err != nil && err != io.EOF {
		return nil, false, err
	}

	mimeType := http.DetectContentType(buffer[:n])
	if !strings.HasPrefix(mimeType, "video/") {
		return nil, false, nil
	}

	ext := strings.ToLower(filepath.Ext(filename))
	videoExtensions := map[string]bool{
		".mp4": true, ".mov": true, ".avi": true, ".mkv": true,
		".webm": true, "wmi": true, "avchd": true, "flv": true,
	}
	if !videoExtensions[ext] {
		return nil, false, nil
	}

	fullReader := io.MultiReader(bytes.NewReader(buffer[:n]), part)
	return fullReader, true, nil
}
