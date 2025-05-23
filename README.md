# Prompts-to-Paper

Writes a paper about hedging a negative AI singularity, using AI.

- `make-paper.py` writes a paper

- `plan0408-piecewise.yaml` contains the prompts

- `make-many-papers.py` runs `make-paper.py` many times.


The README is entirely human-written. Please forgive typos and errors.

-Andrew Chen,  April 9, 2025

# Motivation

On March 8, 2025 I thought I should write a paper about hedging the AI singularity.

I was worked up. I had been repeatedly shocked by AI progress. I was using AI to prove theorems, [vibe coding](https://en.wikipedia.org/wiki/Vibe_coding), and AI lit reviews in my daily life. Six months ago, I had thought each of these things is impossible.

What will happen in the next six years?! Will my entire job be replaced by AI? I have no idea.

But I do know that if there are huge AI disruptions, then tech stocks will most likely benefit. So if anything bad happens to my human capital, I could at least partially hedge. Strangely, I hadn't heard about this concept before.

I asked a friend if he would be interested in working on this paper. Unfortunately, he was busy. So, I thought I should use AI to write the paper. 

## Inspiration

This project was inspired by [Novy-Marx and Velikov (2025)](https://www.nber.org/papers/w33363)  and [Chris Lu et al. (2024)](https://arxiv.org/abs/2408.06292). These projects use AI to generate massive amounts of academic research. My goal differs in quality over quantity. I want to generate just one paper, but one paper that (I hope) people find is worth reading.

This project was also inspired by [Garleanu, Kogan, and Panageas's (2012)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X12000621) beautiful model of innovation and displacement risk. I read Garleanu et al. back when I was a PhD student and it has stuck with me. 

Last, I drew from [Hadfield-Menell and Hadfield (2018)](https://arxiv.org/abs/1804.04268) and [Bengio (2023)](https://www.journalofdemocracy.org/ai-and-catastrophic-risk/), who apply ideas from economics to AI catastrophe risk. [Hadfield-Menell and Hadfield (2018)](https://arxiv.org/abs/1804.04268) explains the connection between incomplete contracting and AI alignment. [Bengio (2023)](https://www.journalofdemocracy.org/ai-and-catastrophic-risk/) frames AI catastrophe risk in terms of what I would call decision theory and human incentives---though the essay is written in plain English. 

Previously, I dismissed "AI safety" as a politicized, activist cause. I still don't like the term "AI safety." "Safety" is such an excuse for exercising power over others. 

But then the nature of AI changed. Things were progressing much faster than I expected. The [Jan 15, 2025 episode of Machine Learning Street Talk with Yoshua Bengio](https://podcasts.apple.com/ca/podcast/yoshua-bengio-designing-out-agency-for-safe-ai/id1510472996?i=1000684132955) left an impression on me. Bengio talked about AI catastrophe risk with no activism, no fear mongering. It was a straight, rational discussion of the seriousness of AI catastrophe risk. 

# The Paper Generation Process

Is this paper really written by AI? 

I’d say the AI are junior co-authors. 

If they were human, I would absolutely have to give o1, Sonnet, and ChatGPT Deep Research credit as co-authors. They did the math, writing, and literature reviews. Sonnet also wrote most of the code (via the Cursor AI IDE).

Of course, the prompts show I did substantial hand-holding. The Github commits show even more human labor. They tell the story of me getting to know my "co-authors." It was hard to communicate style issues and LaTeX instructions, leading to many, many commits.

To be honest, writing this paper would have been much easier if I had done more of the work myself. 

But that can happen with human co-authors too. 

Perhaps in the next few years, AI and humans will be equal co-authors. 

## Paper Iterations

Like human-written papers, the writing process was iterative. The first formalizations were terrible. 

`plan0313-laborshare.yaml` (from March 13) contains prompts for a neoclassical growth model, where the capital share suddenly increases. ChatGPT-o1 [patiently explained to me](https://chatgpt.com/share/67ee989a-50b4-800d-842f-ab71d2424c53) why this is a bad model.

me:
 > I thought there would be a wage risk effect that leads to higher investment for the more risk averse agent. High capital share means low or even no wage income.

ChatGPT-o1:
> Below is an explanation of why one might **expect** a "wage-risk" channel in which **more** risk aversion could lead to **more** *additional* investment (relative to the no-jump benchmark) in the event that the capital share might jump to 1. However, this channel **does not operate** in the usual **representative-agent** version of the model---there, wage and capital income ultimately go to the *same* agent, so there is no meaningful "hedge" of wage risk. 

I went through several iterations of the model with Claude 3.7 Sonnet (thinking mode) and ChatGPT-o1. The only derivations I did myself were to check o1's work, which I found to be quite reliable.

The final `plan0408-piecewise.yaml` uses a simplified Barro-Rietz disaster model, with two agents (though only one is relevant for stock prices). I slowly walk the AIs through the writing, using ten prompts, to maintain the writing quality. 

## Literature Reviews

A key step was generating lit reviews (`./lit-context/`) which were used as context in the prompts. I made lit reviews using ChatGPT's Deep Research (launched Feb 2025) until I ran out of credits. I used Claude Web Search (launched March 20, 2025) for the remainder.

These new products are a game changer. Both [Novy-Marx and Velikov (2025)](https://www.nber.org/papers/w33363)  and [Chris Lu et al. (2024)](https://arxiv.org/abs/2408.06292) ran into hallucinated citations. Building off OpenAI Deep Research and Claude Web Search led to zero hallucinations in the paper drafts.

Still, I would occassionaly run into mis-citations. Every 15 to 20 citations, I would see a cite that mis- or overinterprets the cited paper. I suppose that's not so different than the human-written citation error rate. But I hate [finding misinterpretations in the literature](https://arxiv.org/pdf/2206.15365) so I purposefully limited the number of cites in the paper.

## AI Model Selection 

I found it best to use o1 for theory, and Sonnet for writing. It's well-known that these are the strengths of these two models. 

I briefly tried having Llama 3.1 405b do the writing. It was terrible! The cutting edge models seemed necessary.

I did not try many other models, in order to get this paper out quickly. Gemini 2.5's release, at the end of March 2025, was *hype*. I tried it out briefly and was impressed. But I gritted my teeth and ignored it. AI progress is too fast to update this paper continuously.

## Picking the best of N papers

The writing quality varies across each run. Rather than try to prompt engineer an error free, insightful paper, I decided to just generate N papers and choose the best one.

5 drafts of the paper can be found in `./manyout0408-pdf/`. They're broadly similar and I would be willing to put my name on most of them. 

I ended up choosing `paper-run-05.pdf`. The abstract overemphasizes the model, but otherwise I like the paper. I hope you find the paper worth reading.

# Lessons about Research 

A common response to [Novy-Marx and Velikov (2025)](https://www.nber.org/papers/w33363) is: "people are not ready for this." I heard concerns that peer review will be inundated with AI-generated slop.

Working on this paper gave me a different perspective. It made me think about the fundamentals. I think the fundamentals are the following:

1. Readers want to learn something interesting and true.

2. Readers don't want to check all the math.

3. A system of author reputations makes 1 and 2 possible.

AI-generated papers don't change any of these fundamentals.  Critically, fundamental 3 made me quite wary of putting my name on AI slop. As a result, I don't think AI-generated papers will change much about peer review, at least not the current generation of AI.

## Limitations of the Current AI (April 9, 2025)

This will likely be out of date by the time you read it.

But right now, AI is like a junior co-author with a talent for mathematics and elegant writing, but sub-par economics reasoning. 

For example, Sonnet often fails to recognize that an economic model does not capture an important channel. This is common (no model can capture everything). The standard practice is to dance gingerly around the channel in the writing. A decent PhD student can recognize this. But Sonnet cannot. 

AI also struggles to generate a satisfying economic model on its own. Its models are typically either too simplistic or too complicated.

I opted not to add empirical work or numerically-solved models. AI can do both, but both require connecting to the outside world, and a plethora of technical challenges.

Last, I often found the literature discussions insufficiently careful (as discussed above).

But how long will these limitations last? 

## The Future of AI and Economics Research (Speculative)

At some point, 2024-style economic analysis will be "on tap." You'll be able to go to a chatbot and ask "write me a paper about hedging AI disaster risk," and it will return you something like this paper (probably something much better). 

"Economics on tap" could be a disaster for the economics labor market (could be). It certainly *will* be an extremely cheap substitute for at least some economists' labor. I suppose the questions is whether that will result in a strong substitution away from labor.

The optimistic argument is that AI also *complements* economists' labor. Perhaps, the number of economists will remain the same, but our research output increases in terms of both quantity and quality. 

But there are reasons why total research output is limited. Two key factors in academic publishing are attention and reputation ([Klamer and van Dalen 2001, J of Economic Methodology](https://repub.eur.nl/pub/6875/2001-0221.pdf)). Readers can only pay attention to so many scholars. These scholars, in turn, can only pay attention to so may projects. 

I'm not saying that I *expect* a disaster for the economics labor market.  But even if it's highly unlikely, it's still a scenario that economists should consider. 