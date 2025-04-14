package handler

import "bytes"

type FileWrapper struct {
	*bytes.Reader
}

func (f *FileWrapper) ReadAt(p []byte, off int64) (n int, err error) {
	return f.Reader.ReadAt(p, off)
}

func (f *FileWrapper) Close() error {
	return nil
}
