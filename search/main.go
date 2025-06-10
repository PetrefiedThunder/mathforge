// This Go-based search service queries an Elasticsearch instance.
// It has been designed with robust error handling and detailed logging.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/olivere/elastic/v7"
)

var es *elastic.Client

func init() {
	// Initialize the Elasticsearch client.
	// The URL uses 'elasticsearch' as the service name provided by Docker Compose.
	var err error
	es, err = elastic.NewClient(elastic.SetURL("http://elasticsearch:9200"))
	if err != nil {
		log.Fatalf("Failed to create Elasticsearch client: %v", err)
	}
}

func searchHandler(w http.ResponseWriter, r *http.Request) {
	// Extract query parameter 'q' for the search term.
	q := r.URL.Query().Get("q")
	if q == "" {
		http.Error(w, "Query parameter 'q' is required", http.StatusBadRequest)
		return
	}

	// Execute the search query using Elasticsearch.
	res, err := es.Search().
		Index("repos"). // Specify the index to search.
		Query(elastic.NewQueryStringQuery(q)).
		Do(context.Background())
	if err != nil {
		log.Printf("Search error: %v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Encode the search results in JSON and send to the client.
	if err := json.NewEncoder(w).Encode(res.Hits.Hits); err != nil {
		log.Printf("JSON encoding error: %v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

func main() {
	// Set up the /search endpoint.
	http.HandleFunc("/search", searchHandler)
	fmt.Println("Search service running on :8080")
	// Start the HTTP server.
	log.Fatal(http.ListenAndServe(":8080", nil))
}