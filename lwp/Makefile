LWP=liblwp.a

all: $(LWP)

$(LWP): lwp.o
	ar r $@ lwp.o
	ranlib $@

lwp.o: lwp.c lwp.h
	cc -m32 -Wall -Werror -g -c -o $@ $< 
	cc -S $<

clean:
	-rm -f  $(LWP) lwp.o liblwp.o 
	-rm -f lwp.s

