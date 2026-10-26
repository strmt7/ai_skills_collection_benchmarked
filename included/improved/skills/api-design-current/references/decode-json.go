package httpjson

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
)

// DecodeJSON consumes one typed JSON value within maxBytes. The HTTP server
// retains ownership of closing r.Body. Schema and domain validation follow this.
func DecodeJSON(w http.ResponseWriter, r *http.Request, dst any, maxBytes int64) error {
	if maxBytes <= 0 {
		return errors.New("body byte budget must be positive")
	}
	decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, maxBytes))
	if err := decoder.Decode(dst); err != nil {
		return err
	}
	var extra any
	err := decoder.Decode(&extra)
	if err == io.EOF {
		return nil
	}
	if err != nil {
		return err
	}
	return errors.New("expected one JSON value")
}
