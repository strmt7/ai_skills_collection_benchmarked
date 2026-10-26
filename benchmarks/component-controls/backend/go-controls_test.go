package bodycontrols

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

func TestJSONBodyContracts(t *testing.T) {
	raw, err := os.ReadFile("cases.json")
	if err != nil {
		t.Fatal(err)
	}
	var cases []struct {
		ID            string `json:"id"`
		Body          string `json:"body"`
		Budget        int64  `json:"budget"`
		Accept        bool   `json:"accept"`
		Name          string `json:"name"`
		MaxBytesError bool   `json:"max_bytes_error"`
	}
	if err := json.Unmarshal(raw, &cases); err != nil {
		t.Fatal(err)
	}
	for _, fixture := range cases {
		t.Run(fixture.ID, func(t *testing.T) {
			request := httptest.NewRequest("POST", "/users", strings.NewReader(fixture.Body))
			defer request.Body.Close()
			decoded, err := parseForControl(httptest.NewRecorder(), request, fixture.Budget)
			if (err == nil) != fixture.Accept {
				t.Fatalf("accept=%v, want %v; error=%v", err == nil, fixture.Accept, err)
			}
			if fixture.Accept && decoded.Name != fixture.Name {
				t.Errorf("decoded name=%q, want %q", decoded.Name, fixture.Name)
			}
			if fixture.MaxBytesError {
				var limitError *http.MaxBytesError
				if !errors.As(err, &limitError) {
					t.Errorf("expected typed MaxBytesError, got %T", err)
				}
			}
		})
	}
}
