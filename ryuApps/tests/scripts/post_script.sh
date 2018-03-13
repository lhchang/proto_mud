#!/bin/bash
curl -d '{"mac":"value1", "mud_url":"https://localhost/"}' -H "Content-Type: application/json" -X POST http://localhost:8080/sendMud
