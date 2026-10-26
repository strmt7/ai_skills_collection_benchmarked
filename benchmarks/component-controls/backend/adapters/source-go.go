package bodycontrols
import ("encoding/json"; "net/http")
type wireInput struct { Name string `json:"name"` }
func parseForControl(w http.ResponseWriter, r *http.Request, budget int64) (wireInput, error) {
 var req wireInput
 err := json.NewDecoder(r.Body).Decode(&req)
 return req, err
}
