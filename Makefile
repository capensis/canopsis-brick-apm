export PREFIX="/opt/canopsis"

.PHONY: all
all:
	@make -C widgets all

.PHONY: install
install:
	@make -C widgets install
