#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include "lwp.h"

// data definition
lwp_context lwp_stacks[LWP_PROC_LIMIT];
int round_robin();
schedfun scheduler = round_robin;
unsigned int lwp_processes = 0;
unsigned int pid_assign = 0;
unsigned int running_lwp = LWP_PROC_LIMIT;
bool in_lwp = false;
ptr_int_t *real_esp;

//////////////////////////////////////////////////////////////////////////////// 
// 
// 
//////////////////////////////////////////////////////////////////////////////// 
int new_lwp(lwpfun function, void *arguement, size_t stacksize)
{
    if (lwp_processes == LWP_PROC_LIMIT)
    {
        printf("Error: Maximum number of lwp reached\n");
        return -1;
    }

    // pid
    lwp_stacks[lwp_processes].pid = ++pid_assign;

    // stack
    lwp_stacks[lwp_processes].stack = (ptr_int_t *)malloc(stacksize * (sizeof(ptr_int_t)));
    if (lwp_stacks[lwp_processes].stack == NULL)
    {
        printf("Error: Memory allocation failed\n");
        return -1;
    }

    // stacksize
    lwp_stacks[lwp_processes].stacksize = stacksize;

    // sp
    ptr_int_t *sp, *bbp;
    sp = lwp_stacks[lwp_processes].stack + (stacksize - 1);
    *sp = (ptr_int_t)arguement;
    *(--sp) = (ptr_int_t)lwp_exit;
    *(--sp) = (ptr_int_t)function;
    *(--sp) = 0xffff;
    bbp = sp;
    *(--sp) = 0xffff;
    *(--sp) = 0xffff;
    *(--sp) = 0xffff;
    *(--sp) = 0xffff;
    *(--sp) = 0xffff;
    *(--sp) = 0xffff;
    *(--sp) = (ptr_int_t)bbp;
    lwp_stacks[lwp_processes].sp = sp;

    lwp_processes++;

    return lwp_stacks[lwp_processes].pid;
}

//////////////////////////////////////////////////////////////////////////////// 
// 
// 
//////////////////////////////////////////////////////////////////////////////// 
int lwp_getpid()
{
    if (in_lwp)
        return lwp_stacks[running_lwp].pid;
    return -1;
}

//////////////////////////////////////////////////////////////////////////////// 
// 
// 
//////////////////////////////////////////////////////////////////////////////// 
void lwp_start()
{
    if (lwp_processes == 0)
        return;
    SAVE_STATE();
    GetSP(real_esp);
    if (running_lwp == LWP_PROC_LIMIT)
        running_lwp = scheduler();
    in_lwp = true;
    SetSP(lwp_stacks[running_lwp].sp);
    RESTORE_STATE();
}

//////////////////////////////////////////////////////////////////////////////// 
// 
// 
//////////////////////////////////////////////////////////////////////////////// 
void lwp_stop()
{
    SAVE_STATE();
    GetSP(lwp_stacks[running_lwp].sp);
    in_lwp = false;
    SetSP(real_esp);
    RESTORE_STATE();
}

//////////////////////////////////////////////////////////////////////////////// 
// 
// 
//////////////////////////////////////////////////////////////////////////////// 
void lwp_yield()
{
    SAVE_STATE();
    GetSP(lwp_stacks[running_lwp].sp);
    running_lwp = scheduler();
    SetSP(lwp_stacks[running_lwp].sp);
    RESTORE_STATE();
}

//////////////////////////////////////////////////////////////////////////////// 
// 
// 
//////////////////////////////////////////////////////////////////////////////// 
void lwp_exit()
{
    free(lwp_stacks[running_lwp].stack);

    int i;
    for (i = running_lwp; i < lwp_processes - 1; i++)
        lwp_stacks[i] = lwp_stacks[i + 1];

    --lwp_processes;
    --running_lwp;

    if (lwp_processes)
    {
        running_lwp = scheduler();
        SetSP(lwp_stacks[running_lwp].sp);
        RESTORE_STATE();
    }
    else
        lwp_stop();
}

//////////////////////////////////////////////////////////////////////////////// 
// 
// 
//////////////////////////////////////////////////////////////////////////////// 
void lwp_set_scheduler(schedfun sched)
{
    if (sched)
        scheduler = sched;
}

//////////////////////////////////////////////////////////////////////////////// 
// 
// 
//////////////////////////////////////////////////////////////////////////////// 
int round_robin()
{
    if (running_lwp < lwp_processes - 1)
        return running_lwp + 1;
    return 0;
}
