CFLAGS ?= -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Werror -O2 \
	-fstack-protector-strong -D_FORTIFY_SOURCE=2

.PHONY: all check clean vendor

all: libstrbuf.a

libstrbuf.a: src/strbuf.o
	$(AR) rcs $@ $^

tests/test_strbuf: tests/test_strbuf.c libstrbuf.a
	$(CC) $(CFLAGS) -Isrc -o $@ $^

check: tests/test_strbuf
	./tests/test_strbuf tests/data/greeting.txt

vendor:
	sh vendor/unity/get.sh

clean:
	rm -f src/*.o libstrbuf.a tests/test_strbuf
