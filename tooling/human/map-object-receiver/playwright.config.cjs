const path=require("node:path");
module.exports={testDir:__dirname,testMatch:"browser-proof.spec.cjs",timeout:90000,expect:{timeout:12000},use:{baseURL:"http://127.0.0.1:8787",trace:"off"},projects:[{name:"desktop-1440x1000",use:{viewport:{width:1440,height:1000}}},{name:"mobile-390x844",use:{viewport:{width:390,height:844}}}],outputDir:path.join(__dirname,"test-results")};
