WIDGETSDIR="$(PREFIX)/var/www/canopsis/widgets/"

.PHONY: all
all: scheduler

.PHONY: install
install: scheduler-install

# Widget Scheduler
.PHONY: scheduler scheduler-install

scheduler:
	@echo "[widgets][$@] Nothing to do"

scheduler-install:
	@cp -Rv scheduler $(WIDGETSDIR)
	@chown -R canopsis:canopsis $(WIDGETSDIR)/scheduler

