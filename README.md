# Prompts-to-Paper

This repo writes a paper about hedging a negative AI singularity, using AI.

The README is generated entirely human-written. Please forgive typos and errors.

# Motivation

On March 8, 2025 I thought I should write a paper about hedging the AI singularity.

I was worked up.  I had been repeatedly shocked by AI progress. I was using AI reasoning, vibe coding, and AI lit reviews in my daily life. Six months ago, I had thought each of these things is impossible.

What will happen in the next six months?! Will my entire job be replaced by AI? I have no idea. 

But I do know that if there are huge disruptions, then tech stocks will benefit. So if anything bad happens to my human capital, I could at least partially hedge. Strangely, I hadn't heard about this concept before.

I asked a friend if he would be interested in working on this paper. Unfortunately, he was busy with revision deadlines for the next month. 

So, I thought I should use AI to write the paper. It would be an elegant way to make my point. It would also hint at where the research process is going in this strange age of AI.

This method is clearly inspired by [Novy-Marx and Velikov (2025)](https://www.nber.org/papers/w33363)  and [Chris Lu et al. (2024)](https://arxiv.org/abs/2408.06292). These pioneering works show how AI could generate massive amounts of academic research. My goal here differs in quality over quantity. I wanted to generate just one paper, but one paper that (I hope) people find is worth reading.

# The Paper Generation Process

## Iterations

Like human-written papers, the process was iterative. The first formalizations were terrible. 

`plan0313-laborshare.yaml` writes a paper about a neoclassical growth model, where the capital share suddenly increases. ChatGPT-o1 [patiently explained to me](https://chatgpt.com/share/67ee989a-50b4-800d-842f-ab71d2424c53) why this is a bad model.

me:
 > I thought there would be a wage risk effect that leads to higher investment for the more risk averse agent. High capital share means low or even no wage income.

o1
> Below is an explanation of why one might **expect** a "wage-risk" channel in which **more** risk aversion could lead to **more** *additional* investment (relative to the no-jump benchmark) in the event that the capital share might jump to 1. However, this channel **does not operate** in the usual **representative-agent** version of the model---there, wage and capital income ultimately go to the *same* agent, so there is no meaningful "hedge" of wage risk. Instead, the wage-risk hedge arises naturally if you depart from the pure representative-agent setting (for example, if households receive labor income but must *choose* how much capital they own).

The final `plan0403-streamlined.yaml` uses a simplified Barro-Rietz disaster model, with two agents (though only one is relevant for stock prices). I went through several iterations of this model with Claude 3.7 sonnet (thinking mode) and ChatGPT-o1. The only derivations I did myself were to check o1's work.

## Literature Reviews

A key element was generating lit reviews (`./lit-context`) to give the AI context. I used ChatGPT's Deep Research (launched Feb 2025) until I ran out of credits. Claude Web Search (launched March 2025, after I began the project) did the remainder.

These new products were a game changer. Both [Novy-Marx and Velikov (2025)](https://www.nber.org/papers/w33363)  and [Chris Lu et al. (2024)](https://arxiv.org/abs/2408.06292) ran into hallucinated citations. OpenAI Deep Research and Claude Web Search had no such problems if they were used with care. 

More broadly, knowing how to use which AI and when was helpful for generating a good paper. 

## AI Model Selection 

o1 did the theory, and sonnet thinking did the writing. It's well known that these are the strengths of these two models. 

Sonnet thinking is OK at economic theory. But I found that it was not assertive enough. It led me down wrong paths because it was too eager to come up with some ideas that for my story (even if they did not make sense).  

I briefly tried having Llama 3.1 470b do the writing. It was terrible! It would be extremely difficult to generate a paper worth reading that way. 

I did not try many other models, in order to get this paper out quickly. Gemini 2.5 was released at the end of March 2025. I'd never get the paper finished if I wanted to really try to explore alternative models. 

## Picking the best of N papers

The quality of the writing varies across each run of the code. There is both a good tail and a bad tail. Some drafts, I found quite insightful! Others, had flagrant errors in the economics. 

Rather than try to prompt engineer an error free, insightful paper, I decided to just generate 10 papers and choose the best one. 

Perhaps in 6 months, the very first paper generated with a simple prompt will be error free and insightful. 

# Lessons about Research 

A common response to [Novy-Marx and Velikov (2025)](https://www.nber.org/papers/w33363) is that "people are not ready for this." The peer review process may be inundated with AI-generated papers. Then perhaps peer reviewers will use AI to review papers, creating a bizarre loop of AI communication. It's hard to see where this is going.

Making an AI-generated paper provided me with some perspective. It helped me see the fundamentals of writing academic papers, namely:

1. Readers want to learn something interesting and true.
2. Readers don't want to check all the math.
3. A system of author reputations makes 1 and 2 possible.

"Hedging the AI Singularity" aims to satisfy all of these fundamentals. Critically, I am quite concerned about putting my name on some AI slop. 