PREFIX="/opt/canopsis"
WIDGETSDIR="$(PREFIX)/var/www/canopsis/widgets/"

.PHONY: all
all: scheduler

.PHONY: install
install: all scheduler-install

# Widget Scheduler
.PHONY: scheduler scheduler-install

scheduler:
	@echo "[$@] Nothing to do"

scheduler-install: scheduler
	@cp -Rv scheduler $(WIDGETSDIR)
	@chown -R canopsis:canopsis $(WIDGETSDIR)/scheduler

