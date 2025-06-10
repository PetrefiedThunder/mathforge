package main

import (
  "fmt"
  "net/http"
  "strings"
)

func PreRegister(w http.ResponseWriter, r *http.Request) {
  domain := r.FormValue("email")
  if !(strings.HasSuffix(domain, "@math.org") || strings.HasSuffix(domain, "@physics.org")) {
    http.Error(w, "Registration restricted to Math or Physics domains", http.StatusForbidden)
    return
  }
  fmt.Fprint(w, "OK")
}