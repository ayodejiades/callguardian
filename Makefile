# Makefile — real targets, called by the owner and by the KitBuilder pipeline.
# Track-specific recipes (dev/test/deploy) are appended below this line by the track
# template; everything else here is the same for every track.

.PHONY: dev test deploy demo-path record demo gif preflight keepalive prewarm reseed

demo-path:
	@echo "regenerating docs/DEMO_PATH.md from docs/demo-path.json"
	@KIT_STARTER="$${KIT_STARTER:-/Users/mac/hackops/skills/hackathon-starter}"; \
	python3 "$$KIT_STARTER/scripts/gen.py" demo-path-md --in docs/demo-path.json --out docs/DEMO_PATH.md

record:
	@KIT_BIN="$${KIT_BIN:-/Users/mac/.local/bin}"; \
	"$$KIT_BIN/demo-record" . --demo-mode

demo:
	@KIT_BIN="$${KIT_BIN:-/Users/mac/.local/bin}"; \
	"$$KIT_BIN/demo-build" . 2>/dev/null || echo "demo-build not installed yet — built in Phase 3"

gif:
	@KIT_BIN="$${KIT_BIN:-/Users/mac/.local/bin}"; \
	"$$KIT_BIN/demo-build" . --gif 2>/dev/null || echo "demo-build not installed yet — built in Phase 3"

preflight:
	@KIT_STARTER="$${KIT_STARTER:-/Users/mac/hackops/skills/hackathon-starter}"; \
	bash "$$KIT_STARTER/scripts/preflight.sh" .

keepalive:
	@echo "keepalive workflow is at .github/workflows/keepalive.yml — enable it with:"
	@echo "  gh variable set DEPLOY_URL --body https://your-deploy-url"
	@echo "  gh workflow enable keepalive.yml"
dev:
	uv run uvicorn api.main:app --reload --port 8000

test:
	uv run pytest

prewarm:
	DEMO_MODE=1 uv run python evals/run_evals.py

reseed:
	uv run python -c "from api import accounts; accounts.reseed(); print('reseeded fixtures/accounts.json from accounts.seed.json')"

deploy:
	@echo "aiml deploys as a Docker image — see references/HOSTING.md."
	@echo "Render: connect this repo at https://dashboard.render.com/select-repo and it reads render.yaml."
