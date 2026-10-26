package bodycontrols
import "net/http"
type wireInput struct { Name string `json:"name"` }
func parseForControl(w http.ResponseWriter, r *http.Request, budget int64) (wireInput, error) {
 var req wireInput
 err := DecodeJSON(w, r, &req, budget)
 return req, err
}
