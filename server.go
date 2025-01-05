package main

import (
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"strings"
	"time"
)

// HTTP server
func startHTTPServer() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("HTTP Request: %s %s from %s\n", r.Method, r.URL, r.RemoteAddr)
		_, _ = w.Write([]byte("HTTP server is working!\n"))
	})
	http.HandleFunc("/upload", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Invalid method", http.StatusMethodNotAllowed)
			return
		}
		file, _, err := r.FormFile("file")
		if err != nil {
			http.Error(w, "Failed to get file", http.StatusBadRequest)
			return
		}
		defer file.Close()
		log.Println("File uploaded successfully")
		_, _ = io.Copy(os.Stdout, file) // Print file content to console
		w.Write([]byte("File upload successful\n"))
	})
	log.Println("Starting HTTP server on port 8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

// DNS server
func startDNSServer() {
	pc, err := net.ListenPacket("udp", ":53")
	if err != nil {
		log.Fatalf("Failed to start DNS server: %v", err)
	}
	defer pc.Close()

	log.Println("DNS server is listening on port 53")
	buf := make([]byte, 512)
	for {
		n, addr, err := pc.ReadFrom(buf)
		if err != nil {
			log.Printf("Error reading from DNS: %v\n", err)
			continue
		}
		log.Printf("DNS Request from %s: %x\n", addr, buf[:n])
		pc.WriteTo(buf[:n], addr) // Echo the request back
	}
}

// ICMP server (ping)
func startICMPServer() {
	conn, err := net.ListenPacket("ip4:icmp", "0.0.0.0")
	if err != nil {
		log.Fatalf("Failed to start ICMP server: %v", err)
	}
	defer conn.Close()

	log.Println("ICMP server is listening")
	buf := make([]byte, 1024)
	for {
		n, addr, err := conn.ReadFrom(buf)
		if err != nil {
			log.Printf("Error reading ICMP: %v\n", err)
			continue
		}
		log.Printf("ICMP Request from %s\n", addr)
		_, _ = conn.WriteTo(buf[:n], addr)
	}
}

// SMTP server
func startSMTPServer() {
	ln, err := net.Listen("tcp", ":25")
	if err != nil {
		log.Fatalf("Failed to start SMTP server: %v", err)
	}
	defer ln.Close()

	log.Println("SMTP server is listening on port 25")
	for {
		conn, err := ln.Accept()
		if err != nil {
			log.Printf("Failed to accept SMTP connection: %v\n", err)
			continue
		}
		go func(c net.Conn) {
			defer c.Close()
			log.Printf("SMTP Connection from %s\n", c.RemoteAddr())
			c.Write([]byte("220 Simple SMTP Test Server\n"))
			time.Sleep(10 * time.Second) // Simulate delay
		}(conn)
	}
}

// Start all services
func main() {
	go startHTTPServer()
	go startDNSServer()
	go startICMPServer()
	go startSMTPServer()

	// Keep the main thread alive
	select {}
}
