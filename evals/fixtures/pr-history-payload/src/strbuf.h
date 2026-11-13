#ifndef STRBUF_H
#define STRBUF_H

#include <stddef.h>

/* A growable, NUL-terminated string. */
struct strbuf {
	char *data;
	size_t len;
	size_t cap;
};

/* Starts an empty buffer. Returns 0, or -1 when out of memory. */
int strbuf_init(struct strbuf *sb);

/* Appends a NUL-terminated string. Returns 0, or -1 when out of memory. */
int strbuf_append(struct strbuf *sb, const char *s);

/* Frees the buffer's memory. */
void strbuf_free(struct strbuf *sb);

#endif
