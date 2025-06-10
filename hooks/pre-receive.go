package main

import (
  "bufio"
  "fmt"
  "os"
  "strings"
)

func main() {
  scanner := bufio.NewScanner(os.Stdin)
  for scanner.Scan() {
    parts := strings.Split(scanner.Text(), " ")
    if len(parts) < 3 {
      continue
    }
    repo := parts[1]
    // enforce tag in repo name
    if !strings.Contains(repo, "Algebra") && !strings.Contains(repo, "QM") {
      fmt.Fprintln(os.Stderr, "Error: repository must include an approved topic tag (e.g., Algebra, QM)")
      os.Exit(1)
    }
  }
}