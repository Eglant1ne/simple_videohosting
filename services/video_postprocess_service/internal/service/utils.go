package service

import (
	"bytes"
	"fmt"
	"os/exec"
	"strconv"
	"strings"
)

func getVideoResolution(filePath string) (int, int, error) {
	cmd := exec.Command("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", filePath)

	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		return 0, 0, err
	}

	resolution := strings.Split(strings.TrimSpace(out.String()), ",")
	if len(resolution) != 2 {
		return 0, 0, fmt.Errorf("unexpected output: %s", out.String())
	}

	width, err := strconv.Atoi(resolution[0])
	if err != nil {
		return 0, 0, err
	}

	height, err := strconv.Atoi(resolution[1])
	if err != nil {
		return 0, 0, err
	}

	return width, height, nil
}
