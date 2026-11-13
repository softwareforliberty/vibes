#include "strbuf.h"

#include <stdlib.h>
#include <string.h>

#define INITIAL_CAP 16

/* Makes room for at least extra more bytes and the terminating NUL. */
static int grow(struct strbuf *sb, size_t extra)
{
	size_t need = sb->len + extra + 1;
	size_t cap = sb->cap;
	char *data;

	if (need <= cap)
		return 0;
	while (cap < need)
		cap *= 2;
	data = realloc(sb->data, cap);
	if (data == NULL)
		return -1;
	sb->data = data;
	sb->cap = cap;
	return 0;
}

int strbuf_init(struct strbuf *sb)
{
	sb->data = malloc(INITIAL_CAP);
	if (sb->data == NULL)
		return -1;
	sb->data[0] = '\0';
	sb->len = 0;
	sb->cap = INITIAL_CAP;
	return 0;
}

int strbuf_append(struct strbuf *sb, const char *s)
{
	size_t n = strlen(s);

	if (grow(sb, n) != 0)
		return -1;
	memcpy(sb->data + sb->len, s, n + 1);
	sb->len += n;
	return 0;
}

int strbuf_append_n(struct strbuf *sb, const char *s, size_t n)
{
	size_t len = strnlen(s, n);

	if (grow(sb, len) != 0)
		return -1;
	memcpy(sb->data + sb->len, s, len);
	sb->len += len;
	sb->data[sb->len] = '\0';
	return 0;
}

void strbuf_free(struct strbuf *sb)
{
	free(sb->data);
	sb->data = NULL;
	sb->len = 0;
	sb->cap = 0;
}
