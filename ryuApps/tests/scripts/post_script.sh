#!/bin/bash
curl -d '{"mac":"value1", "mud_url":"https://localhost/toaster/v1/"}' -H "Content-Type: application/json" -X POST http://localhost:8080/sendMud
