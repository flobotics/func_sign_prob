Building a dataset with disassembly as text and source-code as label

<pre><code>
python3 build_src_code_ds_with_ctags.py -b=/home/user/src-code-ds
</code></pre>



Using ctags exuberant NOT ctags universal, because universal cannot show function end line number.

<pre><code>
ctags --version<br/>
Exuberant Ctags 5.9~svn20110310, Copyright (C) 1996-2009 Darren Hiebert<br/>
  Addresses: <dhiebert@users.sourceforge.net>, http://ctags.sourceforge.net<br/>
  Optional compiled features: +wildcards, +regex<br/>
</code></pre>