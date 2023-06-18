#include <stdio.h>
#include <sys/wait.h> 
#include <unistd.h>

#define ITER_MAX 10
#define SLEEP 10.0

int main(void)
{
   char msg_p[] = "parent";
   char msg_c[] = "child";
   char nl[] = "\n";

   for (int i=0; i<ITER_MAX; i++)
   {
      if (fork())
      {
         //usleep(100000);
         /* printf("parent ");  fflush(stdout); */
         // printf(""); 
         // fflush(stdout); 
         // printf("parent ");
         // fflush(stdout); 
         sleep(SLEEP); 
         write(STDOUT_FILENO,msg_p,sizeof(msg_p)-1);
         wait(NULL);
      } else {
         //usleep(100000);
         /* printf("child ");  fflush(stdout); */
         // printf(""); 
         // fflush(stdout); 
         // printf("child ");
         // fflush(stdout); 
         sleep(SLEEP); 
         write(STDOUT_FILENO,msg_c,sizeof(msg_c)-1);
         return 0;
      }

      // usleep(100000);
      /*printf("%i\n",i); fflush(stdout); */
      sleep(SLEEP); 
      write(STDOUT_FILENO,nl,sizeof(nl)-1);
   }

   return 0;
}