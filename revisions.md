Change the project name from Flatfish to Ficherito. Change everywhere we use flatfish to ficherito. 

Change "processes images from HuggingFace datasets" to a local folder of images.

For dates, let's adopt undate as our model for dates https://github.com/dh-tech/undate-python/

Change from Dashscope default to base_url, model name and api key as variables in .env

For the site build, let's use this example: https://github.com/PULdischo/discho-blog
We need to use 11ty, PageFind and Sveltia. The Sveltia config needs to conform to the frontmatter and content in the document image pages.  So we'll be able to make edits to the transcribed text, add/remove entities and so on. 
Include the deploy.yml workflow (assume that final export site will be tracked by github and that we can push to a repo and deploy using github pages. Include documentation for doing this in the docs. )


Keep simple: remove the finding aid steps from the pipeline and from the interface. Same for Key changes dropdown and page. Remove the Research questions feature and menu option in navbar dropdown. Keep browse by date. Keep browse by entity. 

Propose ways to make search loading faster. It currently hangs and the user has to agree to wait to finish loading the index. Are there ways to make this load invisible to the user? 