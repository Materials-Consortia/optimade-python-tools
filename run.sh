#!/bin/bash
uvicorn optimade.server.main:app --reload --port 5000
