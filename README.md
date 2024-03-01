# Mayabatch Executer

A way to optimize workflow is to perform long-running tasks in the background, on a
separate process. AppExecuter provides a facade to using subprocess while also adding
the ability to watch for notifications using threading. I have a version included of a 
MayabatchExecuter that I used for a private project. It can safely run arbitrary python
code, inject code globally, and extracts python errors from the subprocess.
