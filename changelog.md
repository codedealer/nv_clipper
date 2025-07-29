# Changelog

All notable changes to this project will be documented in this file.

## [6.0.1](https://github.com/exwm/yt_clipper/compare/v6.0.0...v6.0.1) (2025-07-13)


### Features

* **clipper:** add explicit colorspace for frame extraction ([6e2ff49](https://github.com/exwm/yt_clipper/commit/6e2ff49f7b3bb36dae06d05f4b4b68167683d4e0))


### Bug Fixes

* **clipper:** color range in RIFE pipe ([6f5ec63](https://github.com/exwm/yt_clipper/commit/6f5ec63eaeb6f3e2d83ef7e610ec1c30515afe17))
* **clipper:** don't set DAR on mjpeg encode ([dfdc7bb](https://github.com/exwm/yt_clipper/commit/dfdc7bb38f7699b8186764ad16fec70e52f1c961))
* **clipper:** force aspect ratio when extracting frames to mjpeg ([ad71326](https://github.com/exwm/yt_clipper/commit/ad713268be6954e710a948c7efaa24ff48325f6f))
* **clipper:** GOP fraction cast ([0d82644](https://github.com/exwm/yt_clipper/commit/0d82644557184c0c62fd7e13fac807eb4fc9602e))
* **clipper:** imprecise trimming when extracting frames for RIFE pipe ([c332828](https://github.com/exwm/yt_clipper/commit/c332828807d9d7f9b2f6190f40ddce0e321934f6))
* **clipper:** interpolation framerate ([8665050](https://github.com/exwm/yt_clipper/commit/86650509b064132a714eb26b862810270ee9d235))
* **clipper:** set framerate before ingesting frames from stdin ([a1a7958](https://github.com/exwm/yt_clipper/commit/a1a79581b2201cb0bf152284955a604ae7acd8bc))


### Documentation Updates

* remove notes ([02f79d5](https://github.com/exwm/yt_clipper/commit/02f79d50398733bdc82bd09dead438810f332b58))

## 6.0.0 (2025-07-09)


### Features

* add border and padding around inputs divs ([dd65fdb](https://github.com/exwm/yt_clipper/commit/dd65fdbf997f7e183ad715aaabf8db2fe6c52ee8))
* auto scale all crops when updating download resolution in defaults ([19522ce](https://github.com/exwm/yt_clipper/commit/19522ce6ba68363da65f40c68b0c74a38469d8a1))
* **clipper/h264:** add --h264-disable-reduce-stutter/--h264-drs flag for opting in to a consistent framerate with duplicate frames when slowing down clips for potentially smoother merged video transitions ([55beecc](https://github.com/exwm/yt_clipper/commit/55beecc52a4ce6c0542a3b19e6c983c7f6c510e9))
* **clipper+markup:** add --enable-hdr option to use high dynamic range for output videos ([75105af](https://github.com/exwm/yt_clipper/commit/75105afa8b019088b5892cb9496ee787ecd5120b))
* **clipper+markup:** add initial support for afreecatv platform vods ([a24b80c](https://github.com/exwm/yt_clipper/commit/a24b80c754763513649b5910307ae8b7c3ae4994))
* **clipper:** add --cookiefile option to pass a cookies file to youtube_dl for video platform login ([33bc588](https://github.com/exwm/yt_clipper/commit/33bc5889c02fd293e86ef9230b2e60171b81be34))
* **clipper:** add --fast-trim/-ft option to generate outputs quickly without re-encoding ([3dbf0f4](https://github.com/exwm/yt_clipper/commit/3dbf0f4b9c69a3b0183b2be078e900fbd220af4e))
* **clipper:** add --log-level option, fix default log level should be VERBOSE not DEBUG ([a1ee47e](https://github.com/exwm/yt_clipper/commit/a1ee47ec9108f4f7753c506ae9352a60736176d0))
* **clipper:** add --video-codec option h264_vulkan for hardware accelerated encodes of h264 ([21a060f](https://github.com/exwm/yt_clipper/commit/21a060fc9cb6e105770b1a93be508d0906040e84))
* **clipper:** add h264_nvenc codec support ([#60](https://github.com/exwm/yt_clipper/issues/60)) ([588b542](https://github.com/exwm/yt_clipper/commit/588b542a6d494ed8f70c7da9f6472120848f506e))
* **clipper:** auto update yt-dlp bundled in frozen releases ([5728875](https://github.com/exwm/yt_clipper/commit/57288752081782d5820af26c5f8a98abd4d58217))
* **clipper:** by default, read args from `../yt_clipper_default_args.txt` for frozen releases ([d00d0b6](https://github.com/exwm/yt_clipper/commit/d00d0b647d8b00e55205efd6ec44233269c7b4dc))
* **clipper:** change default --format-sort option for yt-dlp to prefer premium bitrate formats ([7ab962b](https://github.com/exwm/yt_clipper/commit/7ab962b3a105b196d0ba45500333e0eb9c6530bc))
* **clipper:** enable weverse support ([c9d5c84](https://github.com/exwm/yt_clipper/commit/c9d5c844fae43d67633924141d38c774ef6e2ab6))
* **clipper:** log audio/video formats found by youtube_dl alternative ([7b93636](https://github.com/exwm/yt_clipper/commit/7b93636ff55364ace18c7559227a4a8f8f229c92))
* **clipper:** minor h264_nvenc codec option adjustments ([c303cc7](https://github.com/exwm/yt_clipper/commit/c303cc706b12cbd8b5c5ed0f73e4182a461711e6))
* **clipper:** on failure to parse markers JSON file, print friendlier error messages and debug info ([2c7fc9e](https://github.com/exwm/yt_clipper/commit/2c7fc9e07c52e805187942236f299f0870361a69))
* **clipper:** organize options into groups, use rich-argparse for richer help output ([fa7ac45](https://github.com/exwm/yt_clipper/commit/fa7ac45bf13998722bfa56907d312308c653e93a))
* **clipper:** use binary yt-dlp to enable updating yt-dlp dep independently ([9316fd4](https://github.com/exwm/yt_clipper/commit/9316fd44480c0d93c2718d4a624fdd988f5e4a5d))
* **clipper:** use rich for richer logging ([e673d24](https://github.com/exwm/yt_clipper/commit/e673d24fbf776659199e9c112de50a13a20031db))
* **clipper:** use yt_clipper icon for python exe builds ([1784a07](https://github.com/exwm/yt_clipper/commit/1784a078a9c2f4378648e18e2ad2609681676c20))
* interp ui changes, basic topaz stab support ([19f4d0b](https://github.com/exwm/yt_clipper/commit/19f4d0bcdb8067c4ab5135c6b35c4b00948a8780))
* lock h264_nvenc as the only supported codec ([fe90a66](https://github.com/exwm/yt_clipper/commit/fe90a660e1708d7c8133c80dd187b1c21a6a6a6e))
* loop playback of currently selected marker ([742a655](https://github.com/exwm/yt_clipper/commit/742a655bd2f6f6315649ddd382027c130bebeb42))
* **markup+clipper:** support yt_clipper generic video platform ([ea150e3](https://github.com/exwm/yt_clipper/commit/ea150e3a44559e79e3f25093c0a568447617fb1f))
* **markup:** add Ctrl+Alt+X for previewing crop in modal window ([95693d4](https://github.com/exwm/yt_clipper/commit/95693d43ccffb19637d6c42d93287552006de961))
* **markup:** crop manipulation: allow use of meta key (command on mac) instead of ctrl key ([63ddd76](https://github.com/exwm/yt_clipper/commit/63ddd76f22117ec5d17cf2cd0b20ae43e2ce8b58))
* **markup:** support crop manipulation and drawing when previewing rotation ([bc8a857](https://github.com/exwm/yt_clipper/commit/bc8a85769ad4624991ea916a9b46455945bc4245))
* **markup:** support for platform tv.naver.com ([6de0da4](https://github.com/exwm/yt_clipper/commit/6de0da4a11b8ae8046c5cd4a0786dbec6630849d))
* **platform:** add support for naver_now_watch platform (now.naver.com/watch URLs) ([3b4cbc6](https://github.com/exwm/yt_clipper/commit/3b4cbc62b3571521ff2137dbb54ec29d001ace37))
* **rife:** integrate rife pipeline ([da0e240](https://github.com/exwm/yt_clipper/commit/da0e240df944bc3ceca432c519d9305eae77246e))
* **rife:** pipe frames in pass1 ([4e68123](https://github.com/exwm/yt_clipper/commit/4e68123efa4bea2fc75b7aaff7352c1bcba4e04f))
* topaz interp ([b1a3210](https://github.com/exwm/yt_clipper/commit/b1a321040691d2500d13848084c50dcdce6bae9b))
* topaz stabilization ([cccd01e](https://github.com/exwm/yt_clipper/commit/cccd01eaf86e5d251e94a6b768d8ccf0b5e4ac0e))
* vidstab with Topaz AI filter ([68c2f5a](https://github.com/exwm/yt_clipper/commit/68c2f5a2ce21459400a98259c1979411aa288d4b))


### Bug Fixes

* adjusting markers position for Firefox ([3a8a507](https://github.com/exwm/yt_clipper/commit/3a8a5070a28d09a4b5920a91512927c504a60bfc))
* allow crop res to scale to vertical video at 480p (width = 480) ([d3155be](https://github.com/exwm/yt_clipper/commit/d3155be208cd8f217a3b287df33db0d74ec64076))
* audio streaming session invalidation when using --audio ([b7c9c7c](https://github.com/exwm/yt_clipper/commit/b7c9c7c0f84fb63999ded46bc2f94f473c98b601))
* automatically scaling crop res height to match video height ([10ca871](https://github.com/exwm/yt_clipper/commit/10ca8711860adea292397118f608fc8c4a854175))
* build process: remove parcel-globals dev dependency as the package was removed from npm. ([b5a66e6](https://github.com/exwm/yt_clipper/commit/b5a66e64654db9d07193938b009d3a34a9c76d0c))
* **build:** enable lfs in checkout action ([5410ce4](https://github.com/exwm/yt_clipper/commit/5410ce4b00c288143f16cfd7ab0613cf4c3eba7a))
* change slowdown in marker editor input label to speed ([7fc0365](https://github.com/exwm/yt_clipper/commit/7fc0365b361ece94e7e9cfab784ec7210cc22116))
* **changelog:** incorrect version section headers for markup script ([d2fc1e3](https://github.com/exwm/yt_clipper/commit/d2fc1e3e10ae87a82f0fac789cde2721a729b285))
* **changelog:** incorrect version section headers for markup script ([1536d19](https://github.com/exwm/yt_clipper/commit/1536d196d0e6d3a611c45875e6d71602064ab4c4))
* **changelog:** youtube-dl dependency update incorrectly listed as 2020.06.16.1 not 2020.07.28 ([4805dd8](https://github.com/exwm/yt_clipper/commit/4805dd8bbcf6902200dfc9a1c7de1e33b63ea988))
* **changelog:** youtube-dl dependency update incorrectly listed as 2020.06.16.1 not 2020.07.28 ([ef7fb94](https://github.com/exwm/yt_clipper/commit/ef7fb94cd3d275976582506ef5ba131b47131078))
* CI: trigger builds on push to release branch ([ac9c7dc](https://github.com/exwm/yt_clipper/commit/ac9c7dc3c50af30b09a2afd4d0f13b112d40ee86))
* clipper script: '/' in file names on windows systems not sanitized ([712afbb](https://github.com/exwm/yt_clipper/commit/712afbb09d13ef9ef251bd86ce7c3ba0208f4d4a))
* clipper script: audio sync issues and audio not disabled in preview mode ([9737158](https://github.com/exwm/yt_clipper/commit/973715852777c53efc1630a769b5f57e82ce3c49))
* clipper script: audio syncing issues due to audio start seek not matching video ([341d34d](https://github.com/exwm/yt_clipper/commit/341d34d0b332ff3fa6e30d0e37d133fcfa9c9dbc))
* clipper script: clean invalid file name characters and always use markers json file name for paths ([96f0264](https://github.com/exwm/yt_clipper/commit/96f02646ae7a8eac0b6e7680f845a959596326cc))
* clipper script: colorspace detection for DASH video ([0837716](https://github.com/exwm/yt_clipper/commit/08377167e9fe453218112f75290fba62ec6b3230))
* clipper script: command line usage with ffmpeg deps from path ([ae646a4](https://github.com/exwm/yt_clipper/commit/ae646a4f2fb78f5f4faf8d467cbe342e248408bd))
* clipper script: convert target max bitrate to string for logging ([2785b6f](https://github.com/exwm/yt_clipper/commit/2785b6f79a4a8b9a00be01414cd93d2c8418c841))
* clipper script: crash on print help ([7ba4f57](https://github.com/exwm/yt_clipper/commit/7ba4f5756c3aca13bef01a840cf92977fb31b774))
* clipper script: dash xml file and merge inputs txt not encoded with utf-8 ([0c85d71](https://github.com/exwm/yt_clipper/commit/0c85d71d12fbf602adf1369b4eec86f4c87b18eb))
* clipper script: delete double quotes in video video titles to avoid bad word splitting ([ded905b](https://github.com/exwm/yt_clipper/commit/ded905bc145a2029f69fb042c53aa9da206978c7))
* clipper script: double scaling of target max bitrate when adjusting for crop ([64889f4](https://github.com/exwm/yt_clipper/commit/64889f4691ba3857b4dcd75ee7237f9294eb3a36))
* clipper script: forward reverse loop does not reverse variable-speed speed filter ([5641e1e](https://github.com/exwm/yt_clipper/commit/5641e1e88964a0853a6462349492c0d4ae32cd1a))
* clipper script: help text for fade duration out of sync with defaults in code ([7babb09](https://github.com/exwm/yt_clipper/commit/7babb09702cc0988913332bd37b277d3b3a31f26))
* clipper script: if DASH video do not use ffprobe to detect bitrate as it fails ([076e508](https://github.com/exwm/yt_clipper/commit/076e508602a424ebd4f3b61d0a652ade38c38d89))
* clipper script: improved final video output duration estimation accuracy ([ad99da5](https://github.com/exwm/yt_clipper/commit/ad99da51380b84387056490a61bec646202e7e13))
* clipper script: incorrect identifier usage for __version__ ([ef16414](https://github.com/exwm/yt_clipper/commit/ef16414c43d4019ce99fce52ba8a53fb00911462))
* clipper script: mac ssl verification errors; bundle and use cacert.pem file ([1c50499](https://github.com/exwm/yt_clipper/commit/1c50499aef4476df00b357e214fa53aa07110ac6))
* clipper script: marker pair encode settings not being overriden from global ([d047c42](https://github.com/exwm/yt_clipper/commit/d047c42e4d238dbfa794f0eb791d50d164885b46))
* clipper script: marker pair merge list now has a default value of '' ([ce87c59](https://github.com/exwm/yt_clipper/commit/ce87c591245ea484a75d50032e1a4b57727a80d8))
* clipper script: missing color_space info from ffprobe causes key error ([6241236](https://github.com/exwm/yt_clipper/commit/62412362ca4d2e631a2a1a93b692bbe08c8872ab))
* clipper script: not updated to use new json field (markerPairs) and broken backwards compatibility with older markers json ([682d13b](https://github.com/exwm/yt_clipper/commit/682d13b8b9525085cbb3b78e07a708699cfe83b7))
* clipper script: null bytes not cleaned from potential filenames ([8c53237](https://github.com/exwm/yt_clipper/commit/8c532372eee0327282ccad375eb99d09eddb6093))
* clipper script: only convert ffprobe detected bitrate to int when not None ([d6712f5](https://github.com/exwm/yt_clipper/commit/d6712f592c3769d256534303c003cb94345232d6))
* clipper script: potential input videos include .part files and other multi-extension file names ([2f164bb](https://github.com/exwm/yt_clipper/commit/2f164bb01a60f76456bc9cd4b9b03de8d8625a6d))
* clipper script: preview mode crashes if folder for generated webms does not exist ([f59ec08](https://github.com/exwm/yt_clipper/commit/f59ec08eabf4e2d968667acf77ae7dd6c8d84f8a))
* clipper script: reconnect flags not properly applied to inputs ([b5c3b28](https://github.com/exwm/yt_clipper/commit/b5c3b286d92a55b65e821c5c0702b4dde983fda6))
* clipper script: speed map filter improperly calculated and creating stuttery video ([d18dcd4](https://github.com/exwm/yt_clipper/commit/d18dcd460cf8b13d95067a7463fd6d5f8008a261))
* clipper script: streaming and encoding long audio sometimes loses connection ([8dbc2fa](https://github.com/exwm/yt_clipper/commit/8dbc2fa50534ce2e316f9428dbc13bb2423633d4))
* clipper script: two pass ignored when vidstab active and organize vidstab pass 1 artifacts on disk ([3f51248](https://github.com/exwm/yt_clipper/commit/3f512480daecd5ee56611687ec65a54ccf44cd8d))
* clipper script: two pass mode not receiving filters ([33c02a2](https://github.com/exwm/yt_clipper/commit/33c02a2b9eecc3fef45c292c428c542bf35094a5))
* clipper script: video info fetch with ffprobe not falling back to youtube-dl ([aa6eaa3](https://github.com/exwm/yt_clipper/commit/aa6eaa37d03f9b4023e9dc2e515a071856291aed))
* **clipper:** --video-stabilization-dynamic-zoom arg should store true ([ff2dec3](https://github.com/exwm/yt_clipper/commit/ff2dec31ba7746160638edcecbd30bc8017ce369))
* clipper: excessive auto scaling of crop height/width ([05f98df](https://github.com/exwm/yt_clipper/commit/05f98df2e11f0e093d2422503a5ac38e42e96848))
* **clipper:helper_scripts:win:** check if markers json passed to options helper script ([fc147ee](https://github.com/exwm/yt_clipper/commit/fc147ee90c97fd6fb96add95f2e0303dff517643))
* **clipper:mac:** preview helper script syntax error ([e342f34](https://github.com/exwm/yt_clipper/commit/e342f347ff1be7a126f11bbfb8991d3cbb4d93e3))
* **clipper:mac:** read command in helper scripts could mangle backslashes ([902a4a5](https://github.com/exwm/yt_clipper/commit/902a4a5d22fb97114774b48f249db9ce14552aee))
* **clipper:mac:** syntax error in input_video helper script ([ab6e215](https://github.com/exwm/yt_clipper/commit/ab6e215c24df8339a4d71cd812b5d123fc276a58))
* **clipper:minterp:** decimate duplicate frames before interpolating to avoid stuttering ([618c86d](https://github.com/exwm/yt_clipper/commit/618c86dac0257e71c86bf4964726c0c28df4296e))
* **clipper:win:** options helper script not correctly passing additional options to clipper ([72c63ab](https://github.com/exwm/yt_clipper/commit/72c63ab405d69ff7fb52ec21da30d51dff1006b2))
* **clipper:win:** output filename included extra . before ext in fast_trim helper script ([b9e4770](https://github.com/exwm/yt_clipper/commit/b9e4770995d0617696367cb8a78863f8003e5b86))
* **clipper:win:** vid2gif helper script not safely handling spaces in paths ([001b799](https://github.com/exwm/yt_clipper/commit/001b799040554d5ad688a8c3c8b7a154ab652945))
* **clipper/h264:** add consistent timescale to reduce hanging when merging clips ([352fc46](https://github.com/exwm/yt_clipper/commit/352fc46a725c8ea951c2100bc6a31f0c6d879def))
* **clipper:** `--delay` not applied to speed map and crop map ([1c7b9ea](https://github.com/exwm/yt_clipper/commit/1c7b9ea013c43be3ad894218540ef8be69d90ee5))
* **clipper:** 0-duration crop point pair at the end of dynamic crop map breaks crop filter ([731d3ab](https://github.com/exwm/yt_clipper/commit/731d3ab9956d5aa7b4cb3254e9e038d834a459da))
* **clipper:** add cli args and defaults for minterp mode and fps ([a063f54](https://github.com/exwm/yt_clipper/commit/a063f54be781ec3718b9ddacc9d3ae95738ffe93))
* **clipper:** add executable permissions to yt_clipper.py and macos utility script preprocess_hevc ([232e10f](https://github.com/exwm/yt_clipper/commit/232e10fc16eaf24a3b2fb5b30f8aabbf1a56a5c0))
* **clipper:** add warning and prompt to disable potentially unsupported video download protocols m3u8/m3u8_native ([932368e](https://github.com/exwm/yt_clipper/commit/932368eec74ad6872d8eebb8b79c4dbb7bd49fbf))
* **clipper:** apply extra video filters after speed filter ([efd1f90](https://github.com/exwm/yt_clipper/commit/efd1f905c86b31ebdd14df2412c8ca757a981f8c))
* **clipper:** apply ruff lint fixes ([6257f16](https://github.com/exwm/yt_clipper/commit/6257f161c2cbf91d118205316ac7ee748b3d2b47))
* **clipper:** auto frame dedupe bugs ([89dca9e](https://github.com/exwm/yt_clipper/commit/89dca9ef0657b6b04aa1ebef147851624e10f608))
* **clipper:** auto scaling crops incorrect when crop res > video res ([ad255a7](https://github.com/exwm/yt_clipper/commit/ad255a76ff33d166e25d16cfd94e5ad196cc4984))
* **clipper:** avoid youtube dash manifest to avoid ffmpeg crashes on long manifests ([330038f](https://github.com/exwm/yt_clipper/commit/330038fd34433553689e870a51d9cb2547ce2253))
* **clipper:** checking subs file extension even when subs not requested ([45a5a64](https://github.com/exwm/yt_clipper/commit/45a5a648313dc1e6f747cf897d1732befaa51281))
* **clipper:** clamp ease percent between 0 and 1 ([ced3885](https://github.com/exwm/yt_clipper/commit/ced388511550b4cb00c60f0efafbb92f070e5019))
* **clipper:** clip filenames should be escaped from rich formatting ([5fbdd75](https://github.com/exwm/yt_clipper/commit/5fbdd75cbd99d0fb4f138e6dc89454c35a21751f))
* **clipper:** color codes present in log file summary report ([70c0763](https://github.com/exwm/yt_clipper/commit/70c07637af90ac49f51ad70dd9961b8bedaa564b))
* **clipper:** crash due to incorrect bit rate extraction for dash video ([571bfcb](https://github.com/exwm/yt_clipper/commit/571bfcb077c302b9f6fd3bdc7c67d270af84217d))
* **clipper:** crash on --fast-trim with local input video file, updates python from 3.8 to 3.12 ([ff9675e](https://github.com/exwm/yt_clipper/commit/ff9675e860c77aab21806b78284fbcf73384d646))
* **clipper:** crash on fetching video dash manifest as yt-dlp seems to no longer provide the dash manifest url ([3b77975](https://github.com/exwm/yt_clipper/commit/3b779754f8846e5762f673f686dfd9ef8c31820a))
* **clipper:** crash on input video mode ([155cbf4](https://github.com/exwm/yt_clipper/commit/155cbf430b61cc5ff9706b831a0c6df15e82b867))
* **clipper:** crash on printing help text ([d1668e3](https://github.com/exwm/yt_clipper/commit/d1668e3792d65d4c266f35de301cae5dbb5bdc1b))
* **clipper:** crash on python < 3.9 due to use of lowercase dict for uppercase Dict type ([1d5de2f](https://github.com/exwm/yt_clipper/commit/1d5de2f01ee1a2a816f0531193c2650360ed0bac))
* **clipper:** crash on vertical speed chart section ([7600462](https://github.com/exwm/yt_clipper/commit/7600462d12bfc6621272a09e1af89d5f1400d164))
* **clipper:** crash on video/audio format determination ([c3b7eba](https://github.com/exwm/yt_clipper/commit/c3b7eba4870ae6550e6ac352fb7eb0c4c67616de))
* **clipper:** crash when audio enabled for a marker pair but not enabled globally ([3f725f6](https://github.com/exwm/yt_clipper/commit/3f725f6f7bde63b6b09d59809fc70a5de4afae22))
* **clipper:** disable minterp for sections with fps higher than target fps ([b9c28c0](https://github.com/exwm/yt_clipper/commit/b9c28c073756bcfa839f56335b98a586a1e0d02c))
* **clipper:** disable youtube-dl caching to avoid http 403 errors from stale signatures ([9e61a08](https://github.com/exwm/yt_clipper/commit/9e61a088f95769f6b7ed87e6f591540c67257f20))
* **clipper:** disable youtube-dl caching to avoid http 403 errors from stale signatures ([2b6ae7d](https://github.com/exwm/yt_clipper/commit/2b6ae7d70ea33a4043d0d6961f4f41f898c722aa))
* **clipper:** duplicate definition of getDefaultEncodeSettings ([09d01c0](https://github.com/exwm/yt_clipper/commit/09d01c0a8f3095aef134fc2b430538403a70e04e))
* **clipper:** error on writing subs when subs subdir not present ([a5c5542](https://github.com/exwm/yt_clipper/commit/a5c55426388a261e336f197c84342f46960fad84))
* **clipper:** extra video filters not applied when fwrev loop mode enabled ([387bb63](https://github.com/exwm/yt_clipper/commit/387bb632b6b05fe857e66cc806332e288dc011a3))
* **clipper:** failing to generate clips when titleSuffix has single quotes or unicode (e.g. CJK) chars and video stabilization is enabled ([3643f69](https://github.com/exwm/yt_clipper/commit/3643f69bea5dcafffd95a6bb99e57c600e09ad7c))
* **clipper:** fails to merge clips with single quotes in file path ([ae4ceec](https://github.com/exwm/yt_clipper/commit/ae4ceec132cef907b3a0a5dbcf0af092c89a99d3))
* **clipper:** ffmpeg from path not used when running unfrozen script ([bb77f1b](https://github.com/exwm/yt_clipper/commit/bb77f1b859848f0f6ec8ceab5b06f3c05d61e97c))
* **clipper:** fix ValueError exception with python>=3.11 from ClipperState dataclass decorator ([dc9c937](https://github.com/exwm/yt_clipper/commit/dc9c9375516da7f0393ad46b1d5714493c157856))
* **clipper:** floorToEven input type should include float ([6b45e14](https://github.com/exwm/yt_clipper/commit/6b45e14e63280d66cb4a8e712cb2151f10281ce0))
* **clipper:** force key frame generation ([fcd5f3d](https://github.com/exwm/yt_clipper/commit/fcd5f3d67a6b52afb213504bc667d982443ab757))
* **clipper:** global settings not logged when using input video ([e24df71](https://github.com/exwm/yt_clipper/commit/e24df713e4eac5c88e916ba179657233dc638118))
* **clipper:** h264_vulkan chroma subsampling artifacting and improve compatibility ([ecd5a1f](https://github.com/exwm/yt_clipper/commit/ecd5a1f93ada1dec479f13a0eb7e02d874125e5b))
* **clipper:** help text not printing due to tuple passed for -msp help key ([d937b7e](https://github.com/exwm/yt_clipper/commit/d937b7e4e90202693609235a41767a08618ee7eb))
* **clipper:** holes in regex for printable ffmpeg commands ([792386d](https://github.com/exwm/yt_clipper/commit/792386dbc1856c121ffaa7a03958a371cac8f398))
* **clipper:** improper rotation when rotate value is the string "0" ([fd7aa7a](https://github.com/exwm/yt_clipper/commit/fd7aa7aa94f100f95141f3e98356d85c114b426d))
* **clipper:** include yt_dlp_plugins as source in build as pyinstaller cannot easily dynamically load plugins from PYTHONPATH ([b75ed92](https://github.com/exwm/yt_clipper/commit/b75ed92ce7666dc051410c0fde5e0703ad4488ff))
* **clipper:** incorrect `--preview` help string ([228aca8](https://github.com/exwm/yt_clipper/commit/228aca818c1ec41f39f731adb1434e38ad3ac108))
* **clipper:** incorrect crops due to crop res not being auto scaled and later used to clamp marker crops ([644f1b3](https://github.com/exwm/yt_clipper/commit/644f1b3fa1022917318c721769ccd607e8571dc6))
* **clipper:** input omission regex in ffmpeg command print out not applied to multiple inputs ([98111a1](https://github.com/exwm/yt_clipper/commit/98111a121156226d414d0c59bc04b25b10ee0427))
* **clipper:** input video omission regex from ffmpeg command print out ([9028c63](https://github.com/exwm/yt_clipper/commit/9028c631150560f481957a95835f7906a888349e))
* **clipper:** log files not placed in correct dir ([5339ee3](https://github.com/exwm/yt_clipper/commit/5339ee3c78c534d6f4823b5b5e3e88a2ef9dce4f))
* **clipper:** making clips with local input video broken due to missing Video Type ([9a14f4d](https://github.com/exwm/yt_clipper/commit/9a14f4d7266b764ff8f2aeb5decb69c1cbb0daeb))
* **clipper:** marker pair encode settings overrides shadowed by global ([09f6e6a](https://github.com/exwm/yt_clipper/commit/09f6e6a5d42e5e7cd8d78f1dc2746a8431073ef0))
* **clipper:** minterp always disabled when using minterp enhancements ([e75af74](https://github.com/exwm/yt_clipper/commit/e75af7437ba0fe3670ecb234e991a502becc0023))
* **clipper:** not accounting for first input frame delay in crop and zoompand filters ([b67f6a4](https://github.com/exwm/yt_clipper/commit/b67f6a4c9e6e12fbcd6ce7b51f46d7a441d3bb12))
* **clipper:** not using system ffmpeg when using source clipper script ([70300b0](https://github.com/exwm/yt_clipper/commit/70300b07438265100bafa5475c32ccf257bbb482))
* **clipper:** only warn about ignored unknown warnings when some are provided ([480220f](https://github.com/exwm/yt_clipper/commit/480220f857dda001b7d6305d1872f813b8881ef3))
* **clipper:** output fps not correctly set causing loss of smoothness in some cases ([b588ccd](https://github.com/exwm/yt_clipper/commit/b588ccd0b1c18d49b11edc2516b3097c65be8161))
* **clipper:** pass --cookiefile option as --cookies to yt-dlp ([#54](https://github.com/exwm/yt_clipper/issues/54)) ([0e43f51](https://github.com/exwm/yt_clipper/commit/0e43f5169e62d7ca74361d1f68a308ff4affb1d9))
* **clipper:** printReport may fail to encode utf-8 when writing to log file ([ce939ba](https://github.com/exwm/yt_clipper/commit/ce939bad126f3050c5a19531f330bd4e007965ba))
* **clipper:** pylint no-else-return warnings ([e8f6b8d](https://github.com/exwm/yt_clipper/commit/e8f6b8d52ec089ea53204d9ae4800841d1871ee9))
* **clipper:** reduce panning and zooming jitter due to inexact cropping ([f4ee925](https://github.com/exwm/yt_clipper/commit/f4ee925767bcccf9e17efdc643922e320289ab98))
* **clipper:** remove forcibly fading audio ([d5e61e6](https://github.com/exwm/yt_clipper/commit/d5e61e6577c5615dfb6f96a4216c84e6dbcbcdfc))
* **clipper:** remove improper frame allignment correction in dynamic speed and dynamic crop filter generators ([2b0ecde](https://github.com/exwm/yt_clipper/commit/2b0ecdef09198ba3e136954e13137a4c0a1eda91))
* **clipper:** remove unsharp filter from video stabilization as it corrupts with some video formats (at least av1) ([24e69f0](https://github.com/exwm/yt_clipper/commit/24e69f051697fb06d37eaaebe3028f630e84d760))
* **clipper:** require only one youtube_dl alternative to run, fatally log if specified youtube_dl alternative doesn't exist ([92aecda](https://github.com/exwm/yt_clipper/commit/92aecda79131225cdea0c7dc4438a460871facb2))
* **clipper:** set macos helper scripts as executables ([3f6ef85](https://github.com/exwm/yt_clipper/commit/3f6ef85484dfd90b01c5561ae511c009f0ae4134))
* **clipper:** set yt-dlp location to bundled yt-dlp for frozen releases ([8a80ac1](https://github.com/exwm/yt_clipper/commit/8a80ac133c8ff3ada1950973fe629a0e6e8b98a1))
* **clipper:** some video players refuse to play h264 video due to specifying format `h264` instead of `mp4` when encoding with libx264 ([8606654](https://github.com/exwm/yt_clipper/commit/8606654627f981012b125ce444e31d1d67729d87))
* **clipper:** some yt video formats unavailable when excluding dash manifest ([c2439aa](https://github.com/exwm/yt_clipper/commit/c2439aa5c1bb9411a01dbc8e749cabdabc6d3754))
* **clipper:** ssl errors when downloading video on macos ([f6fa9a7](https://github.com/exwm/yt_clipper/commit/f6fa9a758c0f75577fe125b0fc4dbe2b7843258b))
* **clipper:** stale requirements.txt ([e24c899](https://github.com/exwm/yt_clipper/commit/e24c899e5d74b48d2b771294f9e7cfa7ab461cbf))
* **clipper:** subprocess crash when ffmpeg command is too large ([1260917](https://github.com/exwm/yt_clipper/commit/12609177d5a95514e66921e65b84301643ebf8ad))
* **clipper:** switch youtube_dl to custom fork of youtube_dlc with vlive fixes ([b25211b](https://github.com/exwm/yt_clipper/commit/b25211b26732810b1801f843e72e6d713014f124))
* **clipper:** thresholds for removing duplicate frames with mpdecimate too weak, removing similar frames at high fps ([88974ee](https://github.com/exwm/yt_clipper/commit/88974eeb4dd90cd4e04c6176f8ac85dbcc2a4716))
* **clipper:** update youtube-dl dep to v2020.07.28 for youtube extractor fixes ([f471c33](https://github.com/exwm/yt_clipper/commit/f471c3362111d0492ee8706b27fb0e168c818375))
* **clipper:** update youtube-dl dep to v2020.07.28 for youtube extractor fixes ([d6769a2](https://github.com/exwm/yt_clipper/commit/d6769a217ac0e3acaa26c8834ecdc262fdbfcd03))
* **clipper:** use -fps_mode vfr to fix encoding hang with variable speed mode, add output frameout options for h264 to reduce stutter when video is slowed ([ae3c172](https://github.com/exwm/yt_clipper/commit/ae3c17280dfa8997a68f1d547c1e61afbf75d4a0))
* **clipper:** username xnor password should be passed to youtube-dl ([577aca5](https://github.com/exwm/yt_clipper/commit/577aca56ed443c7c07d6465357e9c2ba5ad0b069))
* **clipper:** using `--extra-ffmpeg-args`/`-efa` without trailing whitespace creates invalid ffmpeg command ([56bff04](https://github.com/exwm/yt_clipper/commit/56bff046135104d00aada3fac18dd1fb0f8bd585))
* **clipper:** vid2gif helper scripts not correctly setting display aspect ratio ([8d3c7ae](https://github.com/exwm/yt_clipper/commit/8d3c7aeec358cb5f43b6dc19a222fc618d82aa38))
* **clipper:** video stabilization fails due to ffmpeg bug ([9255893](https://github.com/exwm/yt_clipper/commit/92558936f57bfaa51dd1ec18ba8835986ccca143))
* **clipper:** video stabilization not working when video filter is large and two-pass is enabled ([cac5c11](https://github.com/exwm/yt_clipper/commit/cac5c11d41386d9501b3249e7266fc56329d62db))
* **clipper:** work around for video stabilization artifacts when input video has low background contrast ([da31b06](https://github.com/exwm/yt_clipper/commit/da31b0646269bba738fba8de99172d6f2f17b3ce))
* **clipper:** youtube_dl alternative imports not overriding global import ([70eb41c](https://github.com/exwm/yt_clipper/commit/70eb41cd66208fc39b25efc833a3b17df2407107))
* **clipper:** zoompan: disable scaling up input when input is HDR before zooming to avoid artifacting ([2c5d0e6](https://github.com/exwm/yt_clipper/commit/2c5d0e6ba5d5ce63c0691a64b07b98052bc015ad))
* crop preview offset when not in theater view ([30025b5](https://github.com/exwm/yt_clipper/commit/30025b50093425f3d9fbe89f3b2c081dbbf22f91))
* crop preview visibility in bright videos ([4433948](https://github.com/exwm/yt_clipper/commit/443394878248c44287d871886245feaeddde0a52))
* crop y offset sometimes did not account for video rect padding ([7fb3ad5](https://github.com/exwm/yt_clipper/commit/7fb3ad5ea5b70f7ca5d6e58aa0696a48ca672d56))
* deleting arbitrary marker pair does not update markers svg indices ([d60048a](https://github.com/exwm/yt_clipper/commit/d60048aa9220f60eef936d11eda3a044cfd03509))
* detection of currently selected marker ([b7a86d7](https://github.com/exwm/yt_clipper/commit/b7a86d71bc43c206d3bd529307abc52bdc49e481))
* docs: bad link to clipper source usage ([1ea473f](https://github.com/exwm/yt_clipper/commit/1ea473f4e1acb0ff5e4810c14c15265fd08bdae3))
* extra dash prefixing title suffix when title prefix is not present ([7233943](https://github.com/exwm/yt_clipper/commit/72339434ae1d487ed4d7812f77c89a32ea693774))
* fetching and encoding best quality stream with dash video and audio ([c22210c](https://github.com/exwm/yt_clipper/commit/c22210cd39ba76e9ac091aa8daf7ec0b76a4dfc1))
* fps detection on videos without a player api script ([4f68f58](https://github.com/exwm/yt_clipper/commit/4f68f5842f0d0ce1b8b5fc76343cd874d4b925ab))
* ignore dir already exists error when creating webm dir ([dab2d84](https://github.com/exwm/yt_clipper/commit/dab2d84805bd6cb41fd65ba328d49805674a5fc3))
* incorrect reporting of crop res height and video height mismatch ([611b924](https://github.com/exwm/yt_clipper/commit/611b924630a7238025d9660de9e0c93bd0712442))
* intended ternary options have no default inherit state ([834c943](https://github.com/exwm/yt_clipper/commit/834c9437803e53f530fb449f4c56f32f9eb55a94))
* invalid audio flag in ffmpeg command ([07c3a9f](https://github.com/exwm/yt_clipper/commit/07c3a9f0a7307932011b0bf5e1dd53e1ed655ec7))
* loading markers .json and then changing crop res could lead to misscaling ([208f41b](https://github.com/exwm/yt_clipper/commit/208f41beb0146cf4cdab2e18fe2d042bc9c6b71d))
* long audio files take very long to begin encoding ([2c291af](https://github.com/exwm/yt_clipper/commit/2c291af5065940148ecfd9c40801292de1bef685))
* make model checks case insensitive ([f10a28f](https://github.com/exwm/yt_clipper/commit/f10a28fc0aa3bd7171618c164c4119ec1d7ec407))
* marker pair crop and slowdown changes do not destroy marker editor html ([065d194](https://github.com/exwm/yt_clipper/commit/065d19414e0f83bf5519cf59768b232104dcc5be))
* marker speed step should be a multiple of 0.05 ([77deb74](https://github.com/exwm/yt_clipper/commit/77deb74ddd45941959976cdbc12572709d36925b))
* markup script: able to add speed points outside speed chart bounds ([51c3876](https://github.com/exwm/yt_clipper/commit/51c3876ee5f290cb58e4cd7fdfe4f3dfa12ec843))
* markup script: active pair detection for slowdown and gamma preview and re-rendering of gamma preview ([abdebae](https://github.com/exwm/yt_clipper/commit/abdebae0604756e7b469394be4b36ca4badd282b))
* markup script: anonymous uploading to gfycat used improper crop format ([307104c](https://github.com/exwm/yt_clipper/commit/307104ced7d792a63108163591a26a54397846e4))
* markup script: auto marker looping occurs even when no marker pair selected ([8fbcbc0](https://github.com/exwm/yt_clipper/commit/8fbcbc08030cbd32cb98e305e731336ca896de80))
* markup script: auto preview updates not frequent enough ([a436dad](https://github.com/exwm/yt_clipper/commit/a436dad1d098874674d9e9ac555d4360cd3232c1))
* markup script: bad cursor position when changing 'ih' crop value and null change amount with ctrl modifier ([37080b1](https://github.com/exwm/yt_clipper/commit/37080b11f609a63994bc4b7cba0874379f5cff05))
* markup script: broken backwards compatibility with older markers json format with markers field ([c3a5bc4](https://github.com/exwm/yt_clipper/commit/c3a5bc4c764e0cba05702ad0ec933682e1ff83e8))
* markup script: browser default and add-on hotkeys could conflict with yt_clipper hotkeys ([ddca1f6](https://github.com/exwm/yt_clipper/commit/ddca1f610576dd25e046361cfe71e5540b0022ef))
* markup script: cannot disable vidstab in pair overrides ([b1c883b](https://github.com/exwm/yt_clipper/commit/b1c883bd4ddb71a808d5f734e51818e7f2e8b1e9))
* markup script: cannot jump between markers that are very close together ([9ea3e1d](https://github.com/exwm/yt_clipper/commit/9ea3e1d9c194202f49e176789bf0ca1954f3d32b))
* markup script: could add or move end markers before start markers and vice versa ([a02386c](https://github.com/exwm/yt_clipper/commit/a02386c3d47bdeabdd6fbe7dff1f215ae48e291a))
* markup script: crop overlay toggling inconsistent logic ([e32490b](https://github.com/exwm/yt_clipper/commit/e32490b2f4016f43cedf73ec803ed8b355fda1e9))
* markup script: default C key bindings such as for copying wrongly disabled ([32fb2d0](https://github.com/exwm/yt_clipper/commit/32fb2d0f81e5d5f40c4f656bb918ad12b6973682))
* markup script: deleted settings showing up in saved markers data as null ([70b033a](https://github.com/exwm/yt_clipper/commit/70b033abb9b435ecc4e646a2d2f6600add70f641))
* markup script: deleting arbitrary marker pair does not delete associated numbering ([cb4368e](https://github.com/exwm/yt_clipper/commit/cb4368e61ff1f6d6b66b82f59352dc7b2bd6f82b))
* markup script: deleting or undoing curr/prev selected marker pair does not clear references to the pair ([56a2395](https://github.com/exwm/yt_clipper/commit/56a2395ec3ab8cea83ba1c9d4e4c0ad1708c9dec))
* markup script: drawing new crop can select text on page ([52ea661](https://github.com/exwm/yt_clipper/commit/52ea661fb2a319a35818d24dc17d8e92b3ffc46b))
* markup script: dynamic zoom setting display not matching internal value ([793f2da](https://github.com/exwm/yt_clipper/commit/793f2daac09c9880602468b3437b9ef1191befff))
* markup script: enable crop adjustment with arrow keys shortcut unintentionally changed ([567f65d](https://github.com/exwm/yt_clipper/commit/567f65d27232c13cc7f60966a4c7db6235f506a3))
* markup script: fade duration placeholder text does not match clipper script default ([4e58d61](https://github.com/exwm/yt_clipper/commit/4e58d61538eb5cec5528232439ada2ce69159e66))
* markup script: fade loop preview not enabled when loop set to fade only globally ([9f8fbf3](https://github.com/exwm/yt_clipper/commit/9f8fbf3304a27ee063f582b5e324bc01a75c0867))
* markup script: fade preview causes crop overlay to disappear ([fe2e17c](https://github.com/exwm/yt_clipper/commit/fe2e17c6b543dba820408c39f8fa86432e8a06bb))
* markup script: fade preview not disabled when set to none in override and fade in global ([20ea473](https://github.com/exwm/yt_clipper/commit/20ea473f06fc2ef023e3c0d6d64060cfc9e348f9))
* markup script: fps detection regex not matching fps with digits not equal to 2 ([958103f](https://github.com/exwm/yt_clipper/commit/958103f562920ef8cbf4268dd4b979278bea4ae2))
* markup script: gamma setting tooltip incorrectly states smallest possible value change ([61a03a4](https://github.com/exwm/yt_clipper/commit/61a03a412f683dbcdc6b8e3befc6f34844f08bfb))
* markup script: handle errors due to unavailable fps information for unprocessed video ([671c3e8](https://github.com/exwm/yt_clipper/commit/671c3e8af2d6f5c4ef6f07f9c3d2d758879707dd))
* markup script: hiding player controls does not hide shadow ([e4e3ad9](https://github.com/exwm/yt_clipper/commit/e4e3ad9c9d349becac420b4d21b8d3009ac70ffd))
* markup script: increasing y offset with arrow keys not clamped ([473c12b](https://github.com/exwm/yt_clipper/commit/473c12b2b11c543c62b86026d4956f1b9e3938b0))
* markup script: initial speed map point not bound to marker pair default speed ([735398b](https://github.com/exwm/yt_clipper/commit/735398ba88b70c164ebf23e5ec14dd17cc3ba44f))
* markup script: interpolated speed values not set to fixed precision after rounding ([3079d80](https://github.com/exwm/yt_clipper/commit/3079d8028ad8c38171842f29ba004383e65c28ec))
* markup script: marker frame skip move could exceed video time bounds ([d2960f6](https://github.com/exwm/yt_clipper/commit/d2960f61e64b256678638ae0772e81c3fe6ff342))
* markup script: marker pair editor and global settings editor ui consistency ([6002bae](https://github.com/exwm/yt_clipper/commit/6002baebc10b43c35e01377288058accc65a7e7e))
* markup script: marker pair editor fade duration placeholder not inheriting from global ([c8ea281](https://github.com/exwm/yt_clipper/commit/c8ea281f8e4304da2b4e4f0fbde2d0164c2a922f))
* markup script: marker pair merge list now maintained when input changed to empty ([e41efb5](https://github.com/exwm/yt_clipper/commit/e41efb5a691bc7240ccb70e5d1283e33d351fc64))
* markup script: marker pair settings not showing inherited default values from global ([621f38a](https://github.com/exwm/yt_clipper/commit/621f38a0c37a69e7fd584ccf53993ca0b46cf990))
* markup script: marker pair speed and crop inputs not updated when updating all pairs to respective default new marker setting ([5f9c443](https://github.com/exwm/yt_clipper/commit/5f9c4439c980d9689abc90d01b6ba914c9a62d9f))
* markup script: markers json loader has poor visiblility in dark mode ([4722317](https://github.com/exwm/yt_clipper/commit/4722317c5961c1aeeecb2987b4bb258c32470079))
* markup script: markers not showing in mainline firefox (lack of svg 2 css) ([c60eaf2](https://github.com/exwm/yt_clipper/commit/c60eaf26eb364215ef342cb4c3c1e7567d2aefc5))
* markup script: missing delete and redo marker pair shortcuts in reference table ([afd87c1](https://github.com/exwm/yt_clipper/commit/afd87c15df9ca7087b020e2e21ca996d5bc4205a))
* markup script: modified marker pair speed and crop highlight lost on editor reload ([03ee54e](https://github.com/exwm/yt_clipper/commit/03ee54e9c5698cfc3538d7785d8bef9523081404))
* markup script: mouse-based crop drag shortcut interfering with marker pair select shortcut ([84658c4](https://github.com/exwm/yt_clipper/commit/84658c49a80662863615973a1561fa783ef8c568))
* markup script: mousewheel scroll blocked by speed chart and interfering with frame skip shortcut ([20152ad](https://github.com/exwm/yt_clipper/commit/20152ad8ebaa84306d546789149caa84c8a15d0b))
* markup script: move marker runs when and just before deactivating hotkeys ([656200a](https://github.com/exwm/yt_clipper/commit/656200a1e5f098ffcd772f77dd7d3a6ca3a50819))
* markup script: new marker defaults not loaded from markers data ([e3b97d9](https://github.com/exwm/yt_clipper/commit/e3b97d90b4a9535ed6bafd936cdef2bf00fdf3c1))
* markup script: pointer event not captured by video causing text selection on crop drag ([c4e67cc](https://github.com/exwm/yt_clipper/commit/c4e67cc04b8b3c538b9bc5fa32e56d84d7a7acaf))
* markup script: prevent drawing crop when speed chart is enabled ([20a00ac](https://github.com/exwm/yt_clipper/commit/20a00acd53622e3df9e5e9297c72ad5c1ef81324))
* markup script: preview prefers shortest active marker pair over currently selected ([8ff46bc](https://github.com/exwm/yt_clipper/commit/8ff46bc82380f7e27d590dc364eb3d2c6625d5b1))
* markup script: reordering marker pairs misarranges markers ([02a078a](https://github.com/exwm/yt_clipper/commit/02a078a1f26a119c48816148f486de2e96b0938c))
* markup script: reordering markers breaks undo marker ([de0e2bd](https://github.com/exwm/yt_clipper/commit/de0e2bd2c1a79aaef92dd73077486af45fb5e9e3))
* markup script: saving and loading of marker pairs (especially for new speed map data) ([45a652b](https://github.com/exwm/yt_clipper/commit/45a652b69468ffc1871799101fa9a031d170efe6))
* markup script: selected marker pair overlay not hard hidden on pair delete or undo ([a0e8a99](https://github.com/exwm/yt_clipper/commit/a0e8a9960eddff724e637ea7a91a57d1086756af))
* markup script: setting speed chart loop markers in FireFox ([5db72bf](https://github.com/exwm/yt_clipper/commit/5db72bf3e0313df396dddd50cf5b7cb17bf469da))
* markup script: settings editors not toggling correctly ([beb86e2](https://github.com/exwm/yt_clipper/commit/beb86e2109c52f761142a08e962ba01f9b521c66))
* markup script: should not be able to delete first or last points of speed chart ([aecb027](https://github.com/exwm/yt_clipper/commit/aecb02736093ec27050db44c7b9259996e030f68))
* markup script: speed adjusted marker pair duration not updated on speed change ([ef5f861](https://github.com/exwm/yt_clipper/commit/ef5f8613adeaac6140c3877c23e32902275d5943))
* markup script: speed chart enabled state not tracked ([83f354f](https://github.com/exwm/yt_clipper/commit/83f354fd2b083673c0b214cd8f151068ad14a18e))
* markup script: speed chart not properly updated on updating all marker pair speeds to default new marker pair speed ([ce02bae](https://github.com/exwm/yt_clipper/commit/ce02bae9952b7b8f02aacf7066816d9c6ad9901d))
* markup script: speed chart pan misbehaving (by updating chart.js 2.9.0 to 2.9.1) ([7b88ac7](https://github.com/exwm/yt_clipper/commit/7b88ac78d90a014e6c72a68c4c488bcdaef9e921))
* markup script: speed chart video time annotation not restarted on show speed chart ([cafbef1](https://github.com/exwm/yt_clipper/commit/cafbef1d778d14515c04a1a24c5741ddd742f12e))
* markup script: start and end speedpoints desync when updated outside of speedchart ([bc7a70d](https://github.com/exwm/yt_clipper/commit/bc7a70d42563359fdbae1b14f275aa39b7a195db))
* markup script: time scaling of fade loop preview with variable speed ([8b1203f](https://github.com/exwm/yt_clipper/commit/8b1203fa64fdc326e3a9fbbe3b1ed1e7919c931c))
* markup script: title suffix could become undefined if left blank ([e81bb1a](https://github.com/exwm/yt_clipper/commit/e81bb1af7bbcbd972d70e4022437b2c77907ca3f))
* markup script: toggling off fade preview does not restore video opacity ([45d8392](https://github.com/exwm/yt_clipper/commit/45d839235a0b77dcbf8a838c7fdfd8afd1c47811))
* markup script: ui not indicating new default speed map rounding of 0 ([98c748f](https://github.com/exwm/yt_clipper/commit/98c748fa66d8972b17391f67d1866efba2b53a51))
* markup script: unable to edit and update new marker default crop ([a133507](https://github.com/exwm/yt_clipper/commit/a1335078be94529f8fb9cd11d2539227a6b193f0))
* markup script: undoing markers when none exist throws errors ([cd08346](https://github.com/exwm/yt_clipper/commit/cd08346b214e12da8f59ff40d8f3910e287769f6))
* markup script: unhandled cases in frame capturer zipping (missing frame capturer window, no frames to zip) ([e412a7a](https://github.com/exwm/yt_clipper/commit/e412a7a521efe072ce36b3526496bb6591a0381b))
* markup script: update speed chart on marker move ([442d97c](https://github.com/exwm/yt_clipper/commit/442d97cfe0f6e3487ace1b3a4421da9286485b53))
* markup script: use precise video time when adding marker ([ea8deb4](https://github.com/exwm/yt_clipper/commit/ea8deb4888b84bb20217d7d62a2793554722c246))
* markup script: vertical alignment of rotated video preview thumbnails ([1fdf0fd](https://github.com/exwm/yt_clipper/commit/1fdf0fd3b2279c3e296e180a1e4641b95b8dc32e))
* markup script: very weak denoise preset causes clipper script crash ([6084e2c](https://github.com/exwm/yt_clipper/commit/6084e2c05bb3ff62a08189daeeb0a44033656891))
* markup script: video playback freezes if speed map loop end before start ([24e0013](https://github.com/exwm/yt_clipper/commit/24e0013f4c343c4ee5b7a5aa191859828d742068))
* markup: alt key causing page to lose focus ([c9c9581](https://github.com/exwm/yt_clipper/commit/c9c958136053559b5867296cff4759e11fe492d0))
* markup: block context menu when ending crop chart time annotation drag ([2324299](https://github.com/exwm/yt_clipper/commit/23242994a857972bf1fb3418359d4deef7ee6817))
* markup: crop section inconsistently maintained when dragging or selecting crop points ([4fdea89](https://github.com/exwm/yt_clipper/commit/4fdea89d5442a22d5365dd719ec6cab26a5f75b1))
* markup: drawing new marker default crop with no marker pairs fails ([e8a025b](https://github.com/exwm/yt_clipper/commit/e8a025ba13b405230bb95d0188677662d9deabc0))
* markup: force set speed improperly updating speed input label ([9aee996](https://github.com/exwm/yt_clipper/commit/9aee9966316cb65a08ad8675b63f5bd108996133))
* markup: gamma filter still active when gamma value is 1 ([ed01bdb](https://github.com/exwm/yt_clipper/commit/ed01bdb81e637e75ca0aa41ab8a19677cefa438e))
* markup: minor typos and misc in tooltips ([07a33f6](https://github.com/exwm/yt_clipper/commit/07a33f6265e5ea98bf543205f01978edbbe87ef5))
* markup: mouse editing crop point crops ([8393f8c](https://github.com/exwm/yt_clipper/commit/8393f8cc35a82533b251916408ae12b29bd4467c))
* markup: stale version number in user script descriptor ([8042ec0](https://github.com/exwm/yt_clipper/commit/8042ec06b7e908a08dd3c0dcb4becbf3a39e7694))
* markup: toggling off editor while dragging crop does not properly close crop overlay ([e45abe7](https://github.com/exwm/yt_clipper/commit/e45abe71c6fa71b52b08d7aa53af2cfc5ec43471))
* markup: track chart enabled state correctly ([2392672](https://github.com/exwm/yt_clipper/commit/2392672c02eda81821966d41d0cb5fb1b8d2fa6d))
* markup: unable to drag default new marker crop ([d513fd6](https://github.com/exwm/yt_clipper/commit/d513fd698c1dcb1da52f45b35ffc813f188ec954))
* markup: video seeking getting stuck ([d39d6b1](https://github.com/exwm/yt_clipper/commit/d39d6b15a6309eb00119869aa2c1d22ddfadc6f0))
* **markup:generic:** speedchart should appear in front of video ([8774747](https://github.com/exwm/yt_clipper/commit/8774747d7dd7319fc10c1d1cf5a2947b3610768e))
* **markup:vlive:** controls background gradient not hidden when mouse manipulating crop ([a686ce1](https://github.com/exwm/yt_clipper/commit/a686ce19df6919e7838ec80426459a991b8c3eba))
* **markup:vlive:** crop res could be invalid if script loaded before content video ([4bda8fc](https://github.com/exwm/yt_clipper/commit/4bda8fc0d1b5982ba6a3885c8337c31afa8ddbfd))
* **markup:vlive:** fails to load video info on video posts ([826c3b3](https://github.com/exwm/yt_clipper/commit/826c3b3ad39037f77a0eece2ee4fe4be30222f50))
* **markup:vlive:** invalid query selectors due to new html structure ([0817a43](https://github.com/exwm/yt_clipper/commit/0817a43d2f9bcfd263069910d78d75f1623437b3))
* **markup:vlive:** left side bar blocking video on small width browser windows ([aeb6709](https://github.com/exwm/yt_clipper/commit/aeb670987dcf7259b747bc1c4af4ad9cc39bc759))
* **markup:vlive:** radio and file inputs not displayed ([d7160c3](https://github.com/exwm/yt_clipper/commit/d7160c3b0e5215bb1e2c98b680203d1ac67c89fc))
* **markup:vlive:** text inputs and text areas triggering hotkeys ([28d2188](https://github.com/exwm/yt_clipper/commit/28d2188d635daf677f536dba247a5969b45cf5fe))
* **markup:vlive:** top region of crop area blocked from manipulation by extraneous click zones ([e18c1d5](https://github.com/exwm/yt_clipper/commit/e18c1d503b5bd327d6d25c6244528c8534bbd398))
* **markup:vlive:** unable to mouse over end marker to select pair ([b771c6b](https://github.com/exwm/yt_clipper/commit/b771c6b410e3f435494595089ff853b5791b0f5a))
* **markup:youtube:** rotated video not properly centered and scaled ([888de37](https://github.com/exwm/yt_clipper/commit/888de373ac4d46a68c167241d7ee3584a95c4791))
* **markup:youtube:** speed chart blocking player progress bar ([18d3131](https://github.com/exwm/yt_clipper/commit/18d31311d0cdd99f97108481922392010f06c1bf))
* **markup:youtube:** video overscaled and cut off in some cases ([47e6eea](https://github.com/exwm/yt_clipper/commit/47e6eeacd41b8fbddf0114db097bafae2d80b44f))
* **markup:youtube:** video seeking not updating progress bar when paused ([bd29fb4](https://github.com/exwm/yt_clipper/commit/bd29fb419a2c2457c06d0adc77d05c72ec391464))
* **markup:** adapt minterp mode input to clipper arg parser ([7cc5c90](https://github.com/exwm/yt_clipper/commit/7cc5c903608acee1812c3845833b13aef8629306))
* **markup:** aspect ratio not updated when changing selected crop point ([20fc619](https://github.com/exwm/yt_clipper/commit/20fc61908d3895fa8cb97417958060ffcaf8084c))
* **markup:** block chart bounds updates until marker numbering drag end ([1749e56](https://github.com/exwm/yt_clipper/commit/1749e56f3b979fc085d0404e6af93045ea362d05))
* **markup:** blocking side bar buttons and content along with side bar pull out ([56ba04d](https://github.com/exwm/yt_clipper/commit/56ba04d58a05767325c85a963c7b8cf31aaa5efd))
* **markup:** bundling creating invalid script ([381ca2a](https://github.com/exwm/yt_clipper/commit/381ca2a239526ed3f1c264dac0d2ad0d89142e38))
* **markup:** chart loop markers not rendering ([28229e6](https://github.com/exwm/yt_clipper/commit/28229e6bb57aa4551c0acc02fc19ea4a77352c06))
* **markup:** chart not updated when switching selected marker pair ([91f9893](https://github.com/exwm/yt_clipper/commit/91f9893f5f0d006d1ba201e1c2fbda3de834b05b))
* **markup:** chart time annotation not properly updated in some cases ([320c579](https://github.com/exwm/yt_clipper/commit/320c5798705c272f9ebf153cd181ab6ba2292ca8))
* **markup:** chartjs annotation plugin not being required due to parcel magic ([8b8aaef](https://github.com/exwm/yt_clipper/commit/8b8aaeff60ef546ff14e0ce53dfe841c93ef7c9f))
* **markup:** crop chart not updated when crop point crop changed ([97154c1](https://github.com/exwm/yt_clipper/commit/97154c1690992fe3dff936e35bc416d2581681a8))
* **markup:** crop chart section and thus dynamic crop preview not updating when crop chart is invisible ([d25eb98](https://github.com/exwm/yt_clipper/commit/d25eb98a48148fe755877d4c7a89669bb8e0f7bf))
* **markup:** crop chart view not updated when current selected crop point or section changes due to video time change ([b2d779e](https://github.com/exwm/yt_clipper/commit/b2d779e63065b35e42a3c4e3a5b440b370d00b81))
* **markup:** crop constraints not applied when manipulating last point of static 2 point crop map ([3df8fe1](https://github.com/exwm/yt_clipper/commit/3df8fe13a6610f4240dbc83e108aa4846bb751d6))
* **markup:** crop constraints not maintained with mouse manipulations on tick where crop has no size delta ([6d1ed3c](https://github.com/exwm/yt_clipper/commit/6d1ed3c960983e8a9a631cea24649a916f2f2173))
* **markup:** crop crosshair not updated when toggled on ([62d3760](https://github.com/exwm/yt_clipper/commit/62d3760cefa184a2b53a917252f149989a0a75a7))
* **markup:** crop crosshair not updating when manipulating global new marker crop ([9747ade](https://github.com/exwm/yt_clipper/commit/9747adeee22c82166fee56dde044eadde1256841))
* **markup:** crop input not updated when current crop point changes ([89cb362](https://github.com/exwm/yt_clipper/commit/89cb36244c92e5607cc5d4d7b921eee2eebda1e4))
* **markup:** crop point formatter incorrectly updated when changing zoom pan override ([0651e29](https://github.com/exwm/yt_clipper/commit/0651e295ed6fda276b4632d8085896b3101ef20c))
* **markup:** crop preview should not use rounded corners ([f577df7](https://github.com/exwm/yt_clipper/commit/f577df77e0f967627eb63470784feca162d5f6d0))
* **markup:** crop res could be invalid if script loaded before video ([3035843](https://github.com/exwm/yt_clipper/commit/30358437b6a66e9a476d1e128398edc74fe1e9a2))
* **markup:** current crop chart section looping bypassed when manipulating crop ([729337a](https://github.com/exwm/yt_clipper/commit/729337a4532a1d2491c6d15eb416e57c1580bd9a))
* **markup:** current crop chart section not looping when interacting with crop with mouse and crop chart invisible ([9471751](https://github.com/exwm/yt_clipper/commit/94717514401e0d7353d35c46d814bc4f0ca89e84))
* **markup:** default crop resolution not matching video aspect ratio ([7c455a9](https://github.com/exwm/yt_clipper/commit/7c455a95a0c5ea97b03d214d1286600df4ac4811))
* **markup:** deleting currently selected crop point changes crop of other points to that of the deleted point ([937773d](https://github.com/exwm/yt_clipper/commit/937773d3725161c1388bfde34eb5d8c9f58c036c))
* **markup:** deleting speed points doesn't update speed input ([bca5e58](https://github.com/exwm/yt_clipper/commit/bca5e588773c5458cd5b1448e6a748957d26fe48))
* **markup:** directly editing crop string of a crop point using improper initial crop values for propagating size change in pan-only mode ([6e5ef59](https://github.com/exwm/yt_clipper/commit/6e5ef5930b22c068200708ab8ed7d25e2cd9c1e3))
* **markup:** do not overwrite video properties in settings when loading markers ([93a020d](https://github.com/exwm/yt_clipper/commit/93a020d37f00491a53e98fe59d6b12abd98994d1))
* **markup:** drawing crop breaking due to use of incorrect crop map index ([c8bc48a](https://github.com/exwm/yt_clipper/commit/c8bc48af4a657b00e33c377c0bea8c4cf86f8e28))
* **markup:** duration estimate always assuming variable speed ([8d347ee](https://github.com/exwm/yt_clipper/commit/8d347eec3fe7e89691917c9476b7e633eb9e00e1))
* **markup:** failing to detect yt watch page due to yt changes ([a427b03](https://github.com/exwm/yt_clipper/commit/a427b037b441f63cc58c942b4db2ba338706f1aa))
* **markup:** fix crash when trusted types are required ([7ceb861](https://github.com/exwm/yt_clipper/commit/7ceb86118c852292f7877e299bd8a10213c6f2c8))
* **markup:** flash messages not accurate when changing zoom pan override ([beb0603](https://github.com/exwm/yt_clipper/commit/beb0603ab48e3301850044fef887376b6310b4c8))
* **markup:** flatten uploaded markers array data to handle nested formats ([89ec890](https://github.com/exwm/yt_clipper/commit/89ec890dfb0275dcb57c5cc7338f78379254f7e7))
* **markup:** force set speed msg not visible when toggling force set speed at speed 1 ([468596c](https://github.com/exwm/yt_clipper/commit/468596c6e087d3e2ffa0c3b0a3f240c49087e201))
* **markup:** force update crop string when inheriting crop point crops and bypass constraints ([6fae997](https://github.com/exwm/yt_clipper/commit/6fae997db9ec7cd586286e58bdb6f64b59c0cbed))
* **markup:** frame capture not scaling correctly when video res does not match crop res ([cbcf7ec](https://github.com/exwm/yt_clipper/commit/cbcf7ec3cbd51da8abc0642737c256b7fdacc56c))
* **markup:** hammerjs conflicts on youtube due to lack of userscript sandboxing ([962964a](https://github.com/exwm/yt_clipper/commit/962964a6ad35a1e1874ac7b367a0ebd6528a63b9))
* **markup:** highlighting speed and crop inputs ([bc65ea4](https://github.com/exwm/yt_clipper/commit/bc65ea414bfdde0fc492c8062a82578f90996092))
* **markup:** invalid script built using parcel possibly due to out of date caniuse dependency ([e1cc981](https://github.com/exwm/yt_clipper/commit/e1cc98188c866d99dd26c9f8eb9417f6f37c3b71))
* **markup:** lag when trying to seek many times in a loop ([51101d7](https://github.com/exwm/yt_clipper/commit/51101d7e2807b4fcba56159cdaf40cd7f4e4891d))
* **markup:** loop previews not updated frequently enough leading to extra frames in preview ([4f11afc](https://github.com/exwm/yt_clipper/commit/4f11afc81e0f45ec66eeabff3397dd801865fb14))
* **markup:** marker numbering pointer events enabled when marker pair hidden ([cad74f7](https://github.com/exwm/yt_clipper/commit/cad74f7e319443d33feafe9b7cf90a418b0b07ec))
* **markup:** marker pair and global settings editors covering up video player ([0e9f06d](https://github.com/exwm/yt_clipper/commit/0e9f06d46d7bfde8df72ac9f0bdc0c7ed45c15a9))
* **markup:** marker pair and global settings editors not displaying, rotate video doesn't fit video into view properly ([3abb89d](https://github.com/exwm/yt_clipper/commit/3abb89d6569acd4fccf1a914c33ef4440a9befad))
* **markup:** marker pair and global settings editors not displaying, rotate video doesn't fit video into view properly, settings editors invisible in non-theatre view mode ([8a2a458](https://github.com/exwm/yt_clipper/commit/8a2a458c5dcc10cc6a8a98bbdbe9fc724f1175a5))
* **markup:** marker pair and global settings editors, flash messages (toasts), shortcuts table not injected just below video ([3edb00e](https://github.com/exwm/yt_clipper/commit/3edb00ebc26f6f6bd70019716faec44b883d7f44))
* **markup:** marker pair duration text not updated when speed chart edited ([d36c190](https://github.com/exwm/yt_clipper/commit/d36c190743e3989075545b377511abf910fa3fc6))
* **markup:** marker pair duration ui text not updated on speed input change ([537afac](https://github.com/exwm/yt_clipper/commit/537afac06ba3ad6ea63d23e7cf819460702e3533))
* **markup:** marker pair looping bypassed when manipulating crop and crop chart not initialized ([be17e79](https://github.com/exwm/yt_clipper/commit/be17e79214e338f62a23aa6222e9a0b5105073df))
* **markup:** marker pair looping crash on video resolution change ([0abae59](https://github.com/exwm/yt_clipper/commit/0abae596da5c91e838994de0629bc3d8a416a5c1))
* **markup:** marker pair selection via mouseover should work on weverse and naver_tv ([8022ac5](https://github.com/exwm/yt_clipper/commit/8022ac5ba6e72b01e76c679bdb6b17fd0650ff38))
* **markup:** marker pair speed not updated when manipulating first speed point ([b9469c7](https://github.com/exwm/yt_clipper/commit/b9469c72e167b7247311f2418a6d860ad131f1d9))
* **markup:** markers data commands menu not closed after loading data ([8adfadc](https://github.com/exwm/yt_clipper/commit/8adfadc50ec61525f43f418d7dfa2dc7c22722d9))
* **markup:** markers with a start or end time of 0 incorrectly loaded ([4dd1aa5](https://github.com/exwm/yt_clipper/commit/4dd1aa573385a2b25f314c932b1022bac841ba0b))
* **markup:** match add point and drag point rounding ([735464d](https://github.com/exwm/yt_clipper/commit/735464dc2ee3ffb070b85b8b14a86ec583d85629))
* **markup:** merge list validation holes ([f3b5101](https://github.com/exwm/yt_clipper/commit/f3b51017f495a87c21145dd960ab878f13eaa826))
* **markup:** min crop size constraint not enforced when drawing crop ([81b6ce2](https://github.com/exwm/yt_clipper/commit/81b6ce296dec8bd6f327bc4f7c1570ed4c847cf8))
* **markup:** minor deviations in final crop when ending mouse resize ([6e5d295](https://github.com/exwm/yt_clipper/commit/6e5d29561a19eaace6768399c71f3e7b84f0188c))
* **markup:** missing some marker numbering mouse shortcuts ([7dd911d](https://github.com/exwm/yt_clipper/commit/7dd911d938f0d3e3c40caa18abee31f07caadacb))
* **markup:** mouse manipulation of new marker crop incorrectly expecting to save marker pair undo state ([bbc6793](https://github.com/exwm/yt_clipper/commit/bbc67935f4383915db11b7df6e95c7e0240ced98))
* **markup:** move marker not removing chart points at target time ([03cf9cc](https://github.com/exwm/yt_clipper/commit/03cf9ccf5ec57422d5819ec8c03ab161db390c69))
* **markup:** no rerender when crop chart section changes without a change in selected point ([73ad6a3](https://github.com/exwm/yt_clipper/commit/73ad6a3e2adcd58c87ef83565e14d075571e01cf))
* **markup:** only seek to new video time when different from current time to avoid unknown perf impact on video player's end ([bf293b3](https://github.com/exwm/yt_clipper/commit/bf293b3f927e8715106aa30eb61fcf7fdb8c8593))
* **markup:** remove unused outputDuration key from saved markers json ([490094f](https://github.com/exwm/yt_clipper/commit/490094feb28e6ca4bc1b7a44ac2258a0a2b0c7ff))
* **markup:** reopening marker pair editor shows static duration estimate even for dynamic speed ([1c9b808](https://github.com/exwm/yt_clipper/commit/1c9b80814e81b5a103ae859faf5eba58ee483659))
* **markup:** search input not disabling hotkeys on focus ([f3ded9e](https://github.com/exwm/yt_clipper/commit/f3ded9edd6b28beca6ecb7043c77ba8bcf3467c4))
* **markup:** set correct mime type for markers json download ([9e8ffa2](https://github.com/exwm/yt_clipper/commit/9e8ffa218f97d0c68bb8db29633bc82709c615fa))
* **markup:** shortcuts table and frame capturer zip progress not working ([87b6e32](https://github.com/exwm/yt_clipper/commit/87b6e326fbd40424b7bc4831cb786edad58ca489))
* **markup:** space key blocked on inputs ([88e0be6](https://github.com/exwm/yt_clipper/commit/88e0be69b2d75a4fea200a29a00cdf2a289959bd))
* **markup:** speed map and speed chart not synced in some cases ([2acddda](https://github.com/exwm/yt_clipper/commit/2acdddaea8989a9d94194c40fc25a0622e8d536e))
* **markup:** start marker numbering not rerendered on start marker move ([2417879](https://github.com/exwm/yt_clipper/commit/241787901d0e3a0dfba930db7934d5a5df5b978b))
* **markup:** switching settings editors would not be able to open the new editor when currently selected crop point was not the first point ([eb0b79e](https://github.com/exwm/yt_clipper/commit/eb0b79e13543812e87d476d0e249791425af513c))
* **markup:** unable to type 'i', 'w', or 'h' in crop input due to auto blurring ([d639020](https://github.com/exwm/yt_clipper/commit/d639020e97e192c6aa7b710071d865690477516a))
* **markup:** update shortcuts reference table ([1c9b9d7](https://github.com/exwm/yt_clipper/commit/1c9b9d7d05e0ac6821552db53e8023536f1258ec))
* **markup:** updating all crop points to maintain crop constraints not updating marker pair crop ([97d86f4](https://github.com/exwm/yt_clipper/commit/97d86f409ab96e4c344ca6bdde9c254e29935a0e))
* **markup:** use common-tags safeHtml over html on innerHTML injection to reduce xss surface ([c1c7257](https://github.com/exwm/yt_clipper/commit/c1c7257e4129c0bb1cf221ab47c6b29a793f773d))
* **markup:** userscript version tag being lost ([f1a23b2](https://github.com/exwm/yt_clipper/commit/f1a23b2c3cada13b3ffba333d62d98e894fb8b6d))
* **markup:** video progress bar and markers should be interactable when speed chart is displaying ([840f078](https://github.com/exwm/yt_clipper/commit/840f07862570f8dc3e3d7bbb5035f360692ff291))
* **markup:** video-crop allignment triggers only on window resize, not video container resize ([ea83170](https://github.com/exwm/yt_clipper/commit/ea83170eab2a89c2a177bd90e5082a6c9469c8cb))
* **markup:** videoURL missing video ID query param ([fa99571](https://github.com/exwm/yt_clipper/commit/fa99571fc59d395bff3ce8817888f2e62c0f196a))
* minor bugs with clipper script ([064b298](https://github.com/exwm/yt_clipper/commit/064b298a8408ba3c114c94d49ee4df4437276965))
* multiple minor bugs in python clipper script ([1763529](https://github.com/exwm/yt_clipper/commit/176352900f24757fa64bb5649869f16f6447d916))
* None valued keys propagating through settings and improper settings cascade ([153355f](https://github.com/exwm/yt_clipper/commit/153355f099b6384b74d6b77a773c8a4b4d416a1e))
* numeric index access of marker type ([e3dfe20](https://github.com/exwm/yt_clipper/commit/e3dfe2059b2453507ac565508a39eb6a7866f62f))
* parse arguments with spaces from argfiles safely ([34aa89f](https://github.com/exwm/yt_clipper/commit/34aa89fed35f44cb884cb52610185364e43c680b))
* parsing crop string when scaling crops to new crop resolution ([a45d2c3](https://github.com/exwm/yt_clipper/commit/a45d2c35b2e5e78836cfb2dc5a35371fdbccdc2c))
* parsing types of marker pair override input values ([1787aac](https://github.com/exwm/yt_clipper/commit/1787aac5ebd2011827e0210196b19ea2ee556387))
* preload DLLs without side-effects ([0f005b5](https://github.com/exwm/yt_clipper/commit/0f005b50c05d980a86d8fc0f0dfb90391e94882a))
* several compile and runtime errors  and add summary report in py clipper script ([f187458](https://github.com/exwm/yt_clipper/commit/f187458533430609218a8b27531b3da460fbec48))
* short title box in defaults editor wider and text aligned right ([cb784da](https://github.com/exwm/yt_clipper/commit/cb784daaeca580b30198f2ae9ff13e6a578dd087))
* **site:** all video load handlers should be disabled after load ([650d759](https://github.com/exwm/yt_clipper/commit/650d7592812da76f17042ebaa5815eb3311142b1))
* slowdowns saved as strings when converting markers to json or string ([849e6d7](https://github.com/exwm/yt_clipper/commit/849e6d763ed86b983bc43b3364c98b601468e83d))
* strongest vidstab preset too strong and producing unpredictable results ([4877726](https://github.com/exwm/yt_clipper/commit/48777263e0198e644a4b9955627fc4a295d64d4d))
* switch to KeyBoardEvent.code to allow either lower or upper case char keys ([e2cc8f4](https://github.com/exwm/yt_clipper/commit/e2cc8f401543ecbdc63cad9b522e53b8dfea252d))
* switch to KeyBoardEvent.code to allow either lower or upper case char keys ([b4e9785](https://github.com/exwm/yt_clipper/commit/b4e9785b4eea4945775b411b07f98ecda44559d9))
* title suffix rewrapped in square brackets when toggling global settings editor ([6bd7829](https://github.com/exwm/yt_clipper/commit/6bd7829393bcfb558c929d4dd6d9737c20974a02))
* toggling auto playback speed ducking ([0a8aa7d](https://github.com/exwm/yt_clipper/commit/0a8aa7def5c672fc702ad204824cfa5180c5be48))
* version of markup script in package.json not updated to 0.0.88 ([44f1b5b](https://github.com/exwm/yt_clipper/commit/44f1b5bb4276d63922ba88d0c70be08b202e410e))
* **wip[10]:zoompan:markup:** only examining first two points for detecting dynamic crop types ([f8d76e9](https://github.com/exwm/yt_clipper/commit/f8d76e99c59d328102a9f369fee5c33e087ecbf2))


### Major Dependency Upgrades

* **clipper:** update ffmpeg dependency to 7.1 (supports vulkan encodes) ([a5959da](https://github.com/exwm/yt_clipper/commit/a5959da0c7e8bf0b1dd21e1e32b9420f6a9b2e9c))
* **clipper:** update ffmpeg to v6.1 ([7ce2052](https://github.com/exwm/yt_clipper/commit/7ce2052ec1ded09a8f1eec9397287a9ae843f2e8))
* **clipper:** update ffmpeg to v7.0.1 ([3c3c534](https://github.com/exwm/yt_clipper/commit/3c3c53456ee2c8a2ce3598e438b22fc19a99480d))
* **clipper:** update yt-dlp dependency from v2023.03.03 to v2023.07.06 ([69c0b34](https://github.com/exwm/yt_clipper/commit/69c0b3417693bcb9a067045cf0ade8f10e51e2e0))
* **clipper:** update yt-dlp dependency from v2023.07.06 to v2023.11.16 ([ccb017a](https://github.com/exwm/yt_clipper/commit/ccb017a45864e28170f68bf024f7fabc6b77c6a0))
* **clipper:** update yt-dlp dependency from v2023.11.16 to v2024.04.09 ([f8a5924](https://github.com/exwm/yt_clipper/commit/f8a592469b6505ee43b3d3e3af7bf3e87c72f359))
* **clipper:** update yt-dlp dependency from v2024.04.09 to v2024.7.25, update pyinstaller from v5.0.1 to v6.9.0 ([a2defb9](https://github.com/exwm/yt_clipper/commit/a2defb927e6cd21fe14cc6e97aefa096ffc148e9))
* **clipper:** update yt-dlp dependency from v2024.08.01 ([9781979](https://github.com/exwm/yt_clipper/commit/9781979a168b16c9815c98a8aa8a481906fba06b))
* **clipper:** update yt-dlp dependency to v2024.08.06 ([02bf7fe](https://github.com/exwm/yt_clipper/commit/02bf7fef04d98b4f7da520841f55b09484710066))
* **clipper:** update yt-dlp dependency to v2024.09.27 ([d06bf12](https://github.com/exwm/yt_clipper/commit/d06bf12a9fdb339cf3b02ba36bd1116e5bdde600))
* **clipper:** update yt-dlp dependency to v2024.10.07 ([d9c8dd5](https://github.com/exwm/yt_clipper/commit/d9c8dd5a88af0f2b93b57a611bfcbc0652e92504))


### Documentation Updates

* add automatic labelling to issue templates ([c2558e3](https://github.com/exwm/yt_clipper/commit/c2558e387b2cc71f52f403eadf690a11d639ed4c))
* add bold to shift+click in hotkey instructions ([0ff96a6](https://github.com/exwm/yt_clipper/commit/0ff96a635d2527862a4b1c2c27f182d85acdd48f))
* add browser support section and hotkey changes (for Firefox and Youtube CC) ([a398d20](https://github.com/exwm/yt_clipper/commit/a398d206fa34e09b71f7bca40b684654f4f89dfd))
* add bug_report.md template ([ff9623d](https://github.com/exwm/yt_clipper/commit/ff9623d13b1c408d594fabeb574bb44d99644718))
* add changelog to readme ([9ebad46](https://github.com/exwm/yt_clipper/commit/9ebad467e5dc88f6567567e415d5b8b1e3a99f16))
* add feature_request.md template ([4a702cb](https://github.com/exwm/yt_clipper/commit/4a702cb514da7481a17dc70b87646bb36d279492))
* add ffmpeg vp9 encoding guide and clarify 0.0.69 changelog ([b5c0c3c](https://github.com/exwm/yt_clipper/commit/b5c0c3c8372c6772b98721e64896efe4af5cf66b))
* add forgotten item in v0.0.71 change log ([7035b7f](https://github.com/exwm/yt_clipper/commit/7035b7f9ce8d934bd0e33dfb7a371d4f0adaf6b3))
* add heading for cropping hotkeys ([a4f361f](https://github.com/exwm/yt_clipper/commit/a4f361f1eaf36ab6e62f85b4a37845c6d58be939))
* add more relevant and focused screenshots and clarify wording ([fe83a32](https://github.com/exwm/yt_clipper/commit/fe83a32d57d96209f1bf9ce240a8c6d1f447d551))
* add pull_request_template.md ([8e15dc9](https://github.com/exwm/yt_clipper/commit/8e15dc960f450f498808ce23621da07b1636ab2b))
* add quickstart guide ([fa5aff3](https://github.com/exwm/yt_clipper/commit/fa5aff3ab8bed0fa0b26b4fa48a708455cbdbe84))
* add quickstart guide ([b66c521](https://github.com/exwm/yt_clipper/commit/b66c5218bcbce00741a353ecaa3790e2f7c44b1f))
* add table of contents and more detail to v0.0.72 change log ([2d0e427](https://github.com/exwm/yt_clipper/commit/2d0e42750a8566e61113d34cc2e5bd444f3c61f6))
* add windows installation and quality/crf settings tips to readme ([1aab31b](https://github.com/exwm/yt_clipper/commit/1aab31bf7bd98ccc5c4f6f83bc78be188eedacab))
* advise windows install users to install visual C++ 2010 redist ([5a12048](https://github.com/exwm/yt_clipper/commit/5a1204896f70b4e3b8dc596a81c753c2a99be0ea))
* **bug_report template:** add sensitive information redaction warning ([1f26236](https://github.com/exwm/yt_clipper/commit/1f26236028c0a2218317c7770e2697fbc4017513))
* **changelog:**  add v3.7.0-beta.4.0.0 notes ([c7f9da4](https://github.com/exwm/yt_clipper/commit/c7f9da48650f8667df9a6af41259dd13b85452c7))
* **changelog:**  add v3.7.0-beta.4.0.0 notes ([8d16ee5](https://github.com/exwm/yt_clipper/commit/8d16ee538a7f895466677bdbff47af45364ed706))
* **changelog:**  add v3.7.0-beta.4.0.1 notes ([4071fc2](https://github.com/exwm/yt_clipper/commit/4071fc26be2e1bc98e3107b568483ce42b88756d))
* **changelog:**  add v3.7.0-beta.4.0.1 notes ([774d66b](https://github.com/exwm/yt_clipper/commit/774d66bcbfbef5a6205676507f59089a298f29cd))
* **changelog:**  add v3.7.0-beta.4.1.0 notes ([a6ec65e](https://github.com/exwm/yt_clipper/commit/a6ec65eacdf919f5cbe47bd9f5385a3b945a4cb0))
* **changelog:**  add v3.7.0-beta.4.1.0 notes ([9fca1c8](https://github.com/exwm/yt_clipper/commit/9fca1c874f68f283ff06556ebeea29ace1182d0e))
* changelog: minor typo ([7410279](https://github.com/exwm/yt_clipper/commit/74102795d13aa68a9cf65500ef8070a21c27304b))
* **changelog:** add clipper v3.6.5 release notes ([c65082f](https://github.com/exwm/yt_clipper/commit/c65082f55e92ab2cf03d804fc20df4afe3a472fa))
* **changelog:** add clipper v3.6.5 release notes ([e0d55a9](https://github.com/exwm/yt_clipper/commit/e0d55a9c5685db2a12000b924e73428d3819da72))
* **changelog:** add notes for v3.7.0-beta.3.9.0-alpha.10 ([d0139bb](https://github.com/exwm/yt_clipper/commit/d0139bb3e806c6a91fe53ed873697916dea3d720))
* **changelog:** add omitted fix from v3.7.0-beta.4.1.0 ([21ffcf7](https://github.com/exwm/yt_clipper/commit/21ffcf74b90fbdf9f899214650a48df082c7ced7))
* **changelog:** add omitted fix from v3.7.0-beta.4.1.0 ([1b9cba0](https://github.com/exwm/yt_clipper/commit/1b9cba0eb01dab53a672e05a99ed649baa4cdd2f))
* **changelog:** add upcoming beta.3.9.0-alpha.7 release ([6744b54](https://github.com/exwm/yt_clipper/commit/6744b54a9b760d2eef11a3f4d37f3d1ea188d6fc))
* **changelog:** add upcoming beta.3.9.0-alpha.7 release ([8ecb7b3](https://github.com/exwm/yt_clipper/commit/8ecb7b33d3efce16279f8daf7a7db50a82007fc8))
* **changelog:** add v3.7.0-beta.3.9.0 notes ([7d3bb5b](https://github.com/exwm/yt_clipper/commit/7d3bb5b3b10637c8b05681f229afb2bb750b6ca3))
* **changelog:** add v3.7.0-beta.3.9.0 notes ([1f1c32d](https://github.com/exwm/yt_clipper/commit/1f1c32df30d77ee460f2679c4bb1938b8b74bf7e))
* **changelog:** add v3.7.0-beta.3.9.0-alpha.11 notes ([fa9a3ce](https://github.com/exwm/yt_clipper/commit/fa9a3ce0559038ed2649e82a440727587dd5c551))
* **changelog:** add v3.7.0-beta.3.9.0-alpha.11 notes ([cf0e992](https://github.com/exwm/yt_clipper/commit/cf0e9922b4ededd912aa94bc1fa24e9a904f91ee))
* **changelog:** add v3.7.0-beta.3.9.0-alpha.12 notes ([3732e2f](https://github.com/exwm/yt_clipper/commit/3732e2feab71a93585370a0c8f3cce0b0d7de7a8))
* **changelog:** add v3.7.0-beta.3.9.0-alpha.12 notes ([a7130b8](https://github.com/exwm/yt_clipper/commit/a7130b819169a4e03151a80279bc1c9d0b26ba6d))
* **changelog:** add v3.7.0-beta.3.9.0-alpha.13 notes ([dfe1324](https://github.com/exwm/yt_clipper/commit/dfe13247f9ad391082e98fab50ba8ce4a82a3071))
* **changelog:** add v3.7.0-beta.3.9.0-alpha.13 notes ([5cfbc9b](https://github.com/exwm/yt_clipper/commit/5cfbc9b8bf30bfa5928cd53dd9df3a3e69f8ffe6))
* **changelog:** add v3.7.0-beta.4.4.0 release notes ([fbf92c1](https://github.com/exwm/yt_clipper/commit/fbf92c1168b32d0ac58aa3f591ad259c382dd3b0))
* **changelog:** add v3.7.0-beta.4.4.0 release notes ([15071e8](https://github.com/exwm/yt_clipper/commit/15071e8caf14b3e0922dc440b22d5dcf13ff1f4c))
* **changelog:** add v3.7.0-beta.4.5.0 release notes ([c7c1f7b](https://github.com/exwm/yt_clipper/commit/c7c1f7b6d1b85810c7688dce81dc9022e8be0be6))
* **changelog:** add v3.7.0-beta.4.5.0 release notes ([af39ca5](https://github.com/exwm/yt_clipper/commit/af39ca54ae38380851cee8a274c94e3f7c0dace9))
* **changelog:** add v5.1.0 release notes ([bc33d3d](https://github.com/exwm/yt_clipper/commit/bc33d3dd23edce09777cb2234fbeb4815fabf582))
* **changelog:** fix a link ([63f40d7](https://github.com/exwm/yt_clipper/commit/63f40d7c8693616c01a71c57109e9bee815f8aca))
* **changelog:** fix minor typo ([4ffec22](https://github.com/exwm/yt_clipper/commit/4ffec22a6b9191d01660dd8391d6801d2442169b))
* **changelog:** fix minor typo ([fbd5bc3](https://github.com/exwm/yt_clipper/commit/fbd5bc3dc9fedb5a8dd4979e7d5c058f62b9b3dc))
* **changelog:** fix not on which version introduced version-unification ([6ad15e8](https://github.com/exwm/yt_clipper/commit/6ad15e81008813b654f52a223bffa322669b966d))
* **changelog:** fix not on which version introduced version-unification ([b4d886e](https://github.com/exwm/yt_clipper/commit/b4d886e16694305076c8098f89a5ed06b5b96612))
* **changelog:** fix some omissions and errors in v3.7.0-beta.3.9.0-alpha.10 notes ([6c62838](https://github.com/exwm/yt_clipper/commit/6c62838a381f14ecef383680489679f1133aa0ea))
* **changelog:** fix typo ([a6b43db](https://github.com/exwm/yt_clipper/commit/a6b43db51033700a0cb95924fbd52a7a6ccb9c56))
* **changelog:** fix typo in v5.6.0 release notes ([744ff6b](https://github.com/exwm/yt_clipper/commit/744ff6bb8f3366a4fb32f3eaf7c435be53ccb574))
* **changelog:** fix v3.7.0-beta.3.9.0-alpha.10 not listed as post version unification ([2908ba7](https://github.com/exwm/yt_clipper/commit/2908ba76bd70105cc0050ed087a8b554560f0fd7))
* **changelog:** fix v3.7.0-beta.3.9.0-alpha.10 not listed as post version unification ([eb56cc5](https://github.com/exwm/yt_clipper/commit/eb56cc5c14f819ae8ab39a61d6bd260dbbe30acd))
* **changelog:** merge file ./changelog.md from branch develop ([37bfefe](https://github.com/exwm/yt_clipper/commit/37bfefe7715caaa6786909fab6a0cfbb6353f880))
* **changelog:** minor corrections ([8226156](https://github.com/exwm/yt_clipper/commit/822615676323dbfffb0f6d9f77a0292354428fcb))
* **changelog:** minor cosmetic fix ([251f343](https://github.com/exwm/yt_clipper/commit/251f3434fa0451ed179ce18d449e81f772fb7ceb))
* **changelog:** minor cosmetic fix ([c95013d](https://github.com/exwm/yt_clipper/commit/c95013d88577524233b29dc528ff23e4ecbd3b2b))
* **changelog:** minor fix for v5.3.0 notes ([8d10efe](https://github.com/exwm/yt_clipper/commit/8d10efef3a575759d5559634189582a4fdbccae9))
* **changelog:** minor fixes ([f4d481d](https://github.com/exwm/yt_clipper/commit/f4d481da3203e84ebe833a58127c5aea62ee3d46))
* **changelog:** minor fixes ([dd0d2d3](https://github.com/exwm/yt_clipper/commit/dd0d2d3f3453a48fa170bbd6f6f10f4bfcd8f458))
* **changelog:** minor fixes ([0d9ff54](https://github.com/exwm/yt_clipper/commit/0d9ff548b281836c5a725c92bf61235551795eac))
* **changelog:** minor fixes ([d04eb47](https://github.com/exwm/yt_clipper/commit/d04eb47ff570366dd2731d4cdefa0c2732b0a10e))
* **changelog:** minor fixes for v3.7.0-beta.4.5.0 notes ([a9bb8ce](https://github.com/exwm/yt_clipper/commit/a9bb8ce7924a98262c2ba990f9abbe42eea8e2a4))
* **changelog:** minor fixes for v3.7.0-beta.4.5.0 notes ([6732332](https://github.com/exwm/yt_clipper/commit/6732332236986db06f0197254a1fa5d6301539cd))
* **changelog:** move pre-version-unification logs to separate file ([2cd5591](https://github.com/exwm/yt_clipper/commit/2cd5591273936ab80e4a71a4a56136a434ec1f13))
* **changelog:** update v5.14.0 notes regarding ffmpeg upgrade ([0ad4fdd](https://github.com/exwm/yt_clipper/commit/0ad4fdd6c4ac300a5f65a5ca55d2fda627706b6a))
* **changelog:** v3.7.0-beta.4.6.0 notes ([4a01986](https://github.com/exwm/yt_clipper/commit/4a019869343cb3846d8873bc245f201bf4815290))
* **changelog:** v3.7.0-beta.4.6.0 notes ([9f432e2](https://github.com/exwm/yt_clipper/commit/9f432e27d575539c6e842b04dd5c0821fae117a6))
* **changelog:** v3.7.0-beta.4.7.0 notes ([78879e4](https://github.com/exwm/yt_clipper/commit/78879e48bb63566d89bfee4f5ee7101e0c874a29))
* **changelog:** v3.7.0-beta.4.7.0 notes ([5410fed](https://github.com/exwm/yt_clipper/commit/5410fed50687889d817ede0dab9dbe184d967891))
* **changelog:** v3.7.0-beta.4.8.0 notes ([be590aa](https://github.com/exwm/yt_clipper/commit/be590aa2ab3eb9da12f5b2adcebea1114518e63f))
* **changelog:** v3.7.0-beta.4.8.0 notes ([15e6b73](https://github.com/exwm/yt_clipper/commit/15e6b735e020c8662344b3143eb87d66c1344745))
* **changelog:** v3.7.0-beta.4.8.1 notes ([be15a08](https://github.com/exwm/yt_clipper/commit/be15a08517785659616d4bbbacb788b19f729cbc))
* **changelog:** v3.7.0-beta.4.8.1 notes ([0dcb773](https://github.com/exwm/yt_clipper/commit/0dcb773a9800c7782b42bc1e9d5d7ab0e67e426f))
* **changelog:** v3.7.0-beta.4.8.2 release notes ([30e6d17](https://github.com/exwm/yt_clipper/commit/30e6d17d2dba26014b6b295d6ce036490a17af3e))
* **changelog:** v3.7.0-beta.4.8.3 release notes ([543079d](https://github.com/exwm/yt_clipper/commit/543079dd6c6dca28447961acc5997eb547ddcb8f))
* **changelog:** v5.0.0 release notes ([d2f9f70](https://github.com/exwm/yt_clipper/commit/d2f9f70aafe5f364802b78bc4594176b5cdb3b1f))
* **changelog:** v5.1.1 release notes ([9dbb6ac](https://github.com/exwm/yt_clipper/commit/9dbb6ac079f75d0e02be8339a8dcc651796bb155))
* **changelog:** v5.1.2 release notes ([ade8e30](https://github.com/exwm/yt_clipper/commit/ade8e3028a6e114b5238a4148ac74abe1c12f7ea))
* **changelog:** v5.1.4 release notes ([70f4877](https://github.com/exwm/yt_clipper/commit/70f4877a2887917c5a0310c05c0718ebe461d29d))
* **changelog:** v5.10.0 release notes ([e3a40da](https://github.com/exwm/yt_clipper/commit/e3a40da3448822b6b091020910b2e7344f674335))
* **changelog:** v5.11.0 release notes ([b4c7ed7](https://github.com/exwm/yt_clipper/commit/b4c7ed7b61b4e1d691a5b5b85844feaed7fe433b))
* **changelog:** v5.11.1 release notes ([a479ddf](https://github.com/exwm/yt_clipper/commit/a479ddfa9c0e96d3de68a7379110bf948e83ead7))
* **changelog:** v5.12.0 release notes ([db55044](https://github.com/exwm/yt_clipper/commit/db55044691d24cc7b029511e3c913e90857253fb))
* **changelog:** v5.2.0 release notes ([2d6d12f](https://github.com/exwm/yt_clipper/commit/2d6d12fdac3523d8b8ee669f3b3c89ca3dcda253))
* **changelog:** v5.2.1 release notes ([f720408](https://github.com/exwm/yt_clipper/commit/f720408e8b520b45a7e7ace91e0336caa55b1f7e))
* **changelog:** v5.3.0 release notes ([753eeba](https://github.com/exwm/yt_clipper/commit/753eebabcb0ef5a2e5196a7a8e29e77e20d7262e))
* **changelog:** v5.3.1 release notes ([c5179c9](https://github.com/exwm/yt_clipper/commit/c5179c9c360dc4e342c0499e53efb72b20ccd795))
* **changelog:** v5.4.0 release notes ([7c1c207](https://github.com/exwm/yt_clipper/commit/7c1c2077f99a3745b299f136b825af7203422e1d))
* **changelog:** v5.4.1 release notes ([a18ecbc](https://github.com/exwm/yt_clipper/commit/a18ecbcdba79a90503e033e476b36a37be091084))
* **changelog:** v5.4.2 release notes ([83c552d](https://github.com/exwm/yt_clipper/commit/83c552d2f8992b0a913573f41ba800119e74bdd1))
* **changelog:** v5.5.0 release notes ([0444477](https://github.com/exwm/yt_clipper/commit/044447788aae4f9cf2a7e71bd20de06b98f43a1d))
* **changelog:** v5.5.1 release notes ([896e74b](https://github.com/exwm/yt_clipper/commit/896e74bb96f5bc896e2c23b59580ce0cd2ef1af8))
* **changelog:** v5.5.2 release notes ([3e0d269](https://github.com/exwm/yt_clipper/commit/3e0d2694332019d80813cb8fdeee91db2dffcce0))
* **changelog:** v5.6.0 release notes ([fe6fe0c](https://github.com/exwm/yt_clipper/commit/fe6fe0c941644d7cd3076062f82467736b22cfd9))
* **changelog:** v5.7.0 release notes ([fc24a52](https://github.com/exwm/yt_clipper/commit/fc24a528afe6e96f505d7d5c8f3124f21d7a5896))
* **changelog:** v5.7.1 release notes ([f111203](https://github.com/exwm/yt_clipper/commit/f1112036b1ac9f19937da08ccd1208e4a620289c))
* **changelog:** v5.8.0 release notes ([13492d3](https://github.com/exwm/yt_clipper/commit/13492d3b02d0bfa7b1c018fe3e54f9ae00d6150e))
* **changelog:** v5.9.0 release notes ([faffb0f](https://github.com/exwm/yt_clipper/commit/faffb0f770d9817fc609e810912cdc52a225538e))
* **changelog:** v5.9.1 release notes ([d3200b9](https://github.com/exwm/yt_clipper/commit/d3200b9d2f9e0ca9880d65782c6a420c590e6284))
* clarify and reorganize changelog for 0.0.71 ([05996d2](https://github.com/exwm/yt_clipper/commit/05996d28eeb95eaf7f83366a1b232961dc10e349))
* clarify auto speed adjustment and auto scaling on download res change ([4d4bbc2](https://github.com/exwm/yt_clipper/commit/4d4bbc2f2406603775eb98b7d3b3597389842a74))
* clarify how to update all markers and cleanup quality and crf tips ([d69b596](https://github.com/exwm/yt_clipper/commit/d69b596c9d1c48a1fa560555c7febf4a192fe2ae))
* clarify shift+mouseover must be done on end marker to select pair ([12757e5](https://github.com/exwm/yt_clipper/commit/12757e50595358eaa4b31a9f7d9e0ca26703f236))
* contributing: add python ver 3 requirement ([59b8044](https://github.com/exwm/yt_clipper/commit/59b804415c902a0cb7d929533a8b997e85eb5228))
* contributing: add python ver 3 requirement ([466dada](https://github.com/exwm/yt_clipper/commit/466dada2436d94d9e79392e00bb6e6ae67858161))
* **contributing:** split markup and clipper script sections, use poetry for markup script ([d9c482a](https://github.com/exwm/yt_clipper/commit/d9c482aab29e37979bb0d47cbe50aa8368882d08))
* fix line number reference for bat file modification ([62fbe3c](https://github.com/exwm/yt_clipper/commit/62fbe3cad4ca61c0e279f13bf2c3937a50a9c19d))
* fix link to clipper script source ([fa9b7ec](https://github.com/exwm/yt_clipper/commit/fa9b7ecbf31402211295b59cd35093ca7fc44926))
* fix minor typos and grammar in quality and crf tips of readme ([4ecffb6](https://github.com/exwm/yt_clipper/commit/4ecffb6e58497996d9e3ae7666ff05f42faa70e8))
* fix typos and clarify changes to hotkeys for Firefox ([c0a2e39](https://github.com/exwm/yt_clipper/commit/c0a2e39016c9e66745a5fbed37a2e5ffec061500))
* fix v3.6.3 release date tag ([47538f4](https://github.com/exwm/yt_clipper/commit/47538f49b3abb3982a0537f074ab2d76296ade78))
* image assets: compress speed chart screenshot ([1a75a67](https://github.com/exwm/yt_clipper/commit/1a75a677cfea7ed411f59afccd13a9b699371182))
* image assets: compress speed chart screenshot ([536a2bb](https://github.com/exwm/yt_clipper/commit/536a2bb9f5750335b93349fe71a2e0b800464f56))
* image assets: update markup script ui screenshots ([3b173f4](https://github.com/exwm/yt_clipper/commit/3b173f4a8206aef4612c266b33a89c47f5373933))
* image assets: update markup script ui screenshots ([6d051e0](https://github.com/exwm/yt_clipper/commit/6d051e00212387abc4bd8cc3e7414e4d6a77fcc3))
* indicate version required for auto looping marker pair in readme ([3f9ced7](https://github.com/exwm/yt_clipper/commit/3f9ced75eef91a4db4dcc70744059da956c42403))
* link to openuserjs instead of greasyfork in readme ([863f9e3](https://github.com/exwm/yt_clipper/commit/863f9e3137971c26a7edbae28c298473bc91b48c))
* minor readme and changelog fixes ([8414e0f](https://github.com/exwm/yt_clipper/commit/8414e0f97fa1dd7756773f89b046d7cdffd9a030))
* proofread and cleanup readme + extract older changelogs to changelog.md ([9a3c68a](https://github.com/exwm/yt_clipper/commit/9a3c68a00885d15439755a93010171035bb7e55a))
* quick start guide: switch changelogs link to user script page section ([4326957](https://github.com/exwm/yt_clipper/commit/4326957cf4cffc441f6dbc984868b3ba7080e086))
* quickstart guide: add where to find generated webms ([e86e04e](https://github.com/exwm/yt_clipper/commit/e86e04e88cb2e412ea4340a3694c6e098c5d2bd3))
* **quickstart:** fix quickstart video tutorial link ([809a5d5](https://github.com/exwm/yt_clipper/commit/809a5d5ca10c6e03d484c96fa1e036707d091294))
* **quickstart:** update to match readme and add video quickstart ([2f7b655](https://github.com/exwm/yt_clipper/commit/2f7b65538c829adfb517af3903a53abd0e5f277d))
* readme: add link to quick start guide ([3a304fd](https://github.com/exwm/yt_clipper/commit/3a304fd289e1cc41b9092171cef273389d359b88))
* readme: add missing change log notes and add markup script install link ([7af438e](https://github.com/exwm/yt_clipper/commit/7af438e69d50c5cf37d46a8841bae1b390a429db))
* readme: add notice about markup script namespace change ([2e98929](https://github.com/exwm/yt_clipper/commit/2e98929cb9e538c234e357e620522cdabbfcc45c))
* readme: add redo undone marker hotkey and update delete pair hotkey ([5497968](https://github.com/exwm/yt_clipper/commit/5497968f36cbf295fd048a443e39b9e0c2153ca9))
* readme: adjust inline screenshot positioning ([c03804e](https://github.com/exwm/yt_clipper/commit/c03804ea7e4e240f4060a08bd7fbcef6630243d5))
* readme: fix hyperlink in terminology section ([79585e9](https://github.com/exwm/yt_clipper/commit/79585e9db416a70b272199797169e504e857bd23))
* readme: fix minor typos and style issues ([bafcd1c](https://github.com/exwm/yt_clipper/commit/bafcd1ccf75e21655c9783ecfd12aa6afa781ccf))
* readme: fix toc links not working in openuserjs ([b4eb57a](https://github.com/exwm/yt_clipper/commit/b4eb57a6423f60553e1faab1c63384e0a7fcaa29))
* readme: minor style and organization fixes ([0130f9a](https://github.com/exwm/yt_clipper/commit/0130f9a59ab22cb7e214bdefd6f5ba36436275fa))
* readme: minor style and organization fixes ([a367fec](https://github.com/exwm/yt_clipper/commit/a367fecc624b27c3bacfa38fb57bd694014828b6))
* readme: replace imgur links with github raw asset links ([735eb0f](https://github.com/exwm/yt_clipper/commit/735eb0fa58872fba9c573f94f0005e8cbe907d39))
* readme: update links for clipper script v3.4.1 and fix old releases link ([8beb3ee](https://github.com/exwm/yt_clipper/commit/8beb3eec4ca15d7f8f89ca0ae07f4062dedffe9b))
* readme: update non-binary clipper script usage ([435ad84](https://github.com/exwm/yt_clipper/commit/435ad84dec4c84ce90a63ff30885c0ef9040dfbe))
* readme: update related scripts section with gfy-tools ([f4b95bd](https://github.com/exwm/yt_clipper/commit/f4b95bd7dd38141ced4c313f92c6fcec3b21a96c))
* **readme:** add link to common shortcuts in dynamic speed and crop shortcut sections ([1d7a6af](https://github.com/exwm/yt_clipper/commit/1d7a6af851110989aff68b8f585f2bade826c006))
* **readme:** add notice about readme being synchronized only to mainline releases ([edcf8f9](https://github.com/exwm/yt_clipper/commit/edcf8f9d9342540f956b0edc96aa599f6c8491ae))
* **readme:** add notice about readme being synchronized only to mainline releases ([5b3ede8](https://github.com/exwm/yt_clipper/commit/5b3ede8277d81709e5995f0552b5b79d161472a5))
* **readme:** add section on clipper default argument files ([d97a06f](https://github.com/exwm/yt_clipper/commit/d97a06f833f2d00340c590dfb0f03553212bbe89))
* **readme:** add section on supported video codecs ([a30b006](https://github.com/exwm/yt_clipper/commit/a30b006190bb13518138ac4e1b646efb30026870))
* **readme:** add section on utility scripts, add help on using merge utility script on mac ([a511d5d](https://github.com/exwm/yt_clipper/commit/a511d5d994aa16078b0f9d2ef0deaa3f218e9615))
* **readme:** add some shortcuts and tips for dynamic crop ([215b535](https://github.com/exwm/yt_clipper/commit/215b5357d0df0c320998e56080d9ffe2a5fd3a47))
* **readme:** add v3.6.3 release ([6251617](https://github.com/exwm/yt_clipper/commit/62516175cf5f3ea49b60bb9a7b5059fbef0c17e2))
* **readme:** add v3.7.0-beta.4.2.0 release notes ([8691b15](https://github.com/exwm/yt_clipper/commit/8691b15c44202e3e1b70dcfc02cdc49b3e0c9872))
* **readme:** add v3.7.0-beta.4.2.0 release notes ([4e5bb5e](https://github.com/exwm/yt_clipper/commit/4e5bb5e0a44d0613a4a9cfb08aa487568d9eb28b))
* **readme:** add v3.7.0-beta.4.3.0 release notes ([becec23](https://github.com/exwm/yt_clipper/commit/becec23de0c70efa5189211b78dfede4623346af))
* **readme:** add v3.7.0-beta.4.3.0 release notes ([e48707c](https://github.com/exwm/yt_clipper/commit/e48707c22e39892877b870948059a744854982b2))
* **readme:** change old releases section to all releases ([ff8f335](https://github.com/exwm/yt_clipper/commit/ff8f335689ac8ab5cd34bfaf207e6b4217a8dd50))
* **readme:** cleanup partial changelog ([9001a0d](https://github.com/exwm/yt_clipper/commit/9001a0d7b82e637aeed7d61da302a0a91f34ecad))
* **readme:** fix links to releases ([4e856fb](https://github.com/exwm/yt_clipper/commit/4e856fbff937a18869b247c95fae24d8cf1b3e89))
* **readme:** fix links to releases ([3fdf708](https://github.com/exwm/yt_clipper/commit/3fdf7081f18e91e7ecf43571f0e609f37494f093))
* **readme:** fix minor type ([33f16e3](https://github.com/exwm/yt_clipper/commit/33f16e3caedfd04c8c1b90d68716cb75e1dc2504))
* **readme:** fix some links in quickstart guide ([b76844a](https://github.com/exwm/yt_clipper/commit/b76844af037692327b629626a97ed081f9b2f4d6))
* **readme:** fix some organization issues ([e9adee9](https://github.com/exwm/yt_clipper/commit/e9adee9d92da97c79b840d1d8d84dfb42a9af877))
* **readme:** inline quick start guide ([5bb87f2](https://github.com/exwm/yt_clipper/commit/5bb87f22cd067d08cf304aa73af803cba755ee37))
* **readme:** minor cleanup ([26381a8](https://github.com/exwm/yt_clipper/commit/26381a817c60c3897833ec8a54f7fb989cecd252))
* **readme:** minor fixes ([6680d36](https://github.com/exwm/yt_clipper/commit/6680d3673a8984e857e8afec7e91955d20c1e40d))
* **readme:** remove extraneous link in inline quickstart guide ([f92a3c8](https://github.com/exwm/yt_clipper/commit/f92a3c8f03c8a301ea37d8b9380a604bda2ddf06))
* **readme:** remove inline changelog ([bcc0f2f](https://github.com/exwm/yt_clipper/commit/bcc0f2f98bf54acd99d8b6b1966772e9b583abc2))
* **readme:** remove inline changelog ([9c5b53b](https://github.com/exwm/yt_clipper/commit/9c5b53bbc8460fcf50d6d89fa7b3e9e6b13d1cfe))
* **readme:** reorganize and rename sections ([2eab1ab](https://github.com/exwm/yt_clipper/commit/2eab1ab1b24d3dddc23fab0f4ed39c99d6eced37))
* **readme:** reorganize dynamic speed and crop sections ([6d4c0c8](https://github.com/exwm/yt_clipper/commit/6d4c0c8226ef5e22a84784def1636713f947fb27))
* **readme:** update beta releases notice ([5530eb6](https://github.com/exwm/yt_clipper/commit/5530eb6353b3b1e34d724a5ba6b80c9acd14f994))
* **readme:** update clipper install links and changelog for clipper v3.6.4 ([b18bde5](https://github.com/exwm/yt_clipper/commit/b18bde5b7dbbab30bbc969ed072179fae3957f8d))
* **readme:** update clipper install links and changelog for clipper v3.6.4 ([f7b1993](https://github.com/exwm/yt_clipper/commit/f7b1993ffa94b121445e04eda1b522739c324103))
* **readme:** update clipper installation links ([073c66a](https://github.com/exwm/yt_clipper/commit/073c66adb4662b714a2acd8afb835a94c1054043))
* **readme:** update clipper installation links ([4742088](https://github.com/exwm/yt_clipper/commit/4742088448aa78bdd87e1333b7c3eab0b008053d))
* **readme:** update clipper script dependencies section ([e41d5ef](https://github.com/exwm/yt_clipper/commit/e41d5ef7628ec720c6155bba4db166b54c4bea9e))
* **readme:** update for beta changes focusing on dynamic crop ([ba8737c](https://github.com/exwm/yt_clipper/commit/ba8737cf317561ab7f61870394dbbed0df17d5a1))
* **readme:** update notices ([8ebb315](https://github.com/exwm/yt_clipper/commit/8ebb3151756e399336b89abfd4e76726f18b3e15))
* **readme:** update overview and some links ([b0124f5](https://github.com/exwm/yt_clipper/commit/b0124f5728b958b00a60469a26ae4a3d9f8f47b3))
* **readme:** update quickstart video link ([1e20605](https://github.com/exwm/yt_clipper/commit/1e20605d68404268183f135caba89e190b5e6756))
* reorganize readme for clarity and consistency ([0dfde32](https://github.com/exwm/yt_clipper/commit/0dfde32abd524005ce0140aa8b57e4674b85f8b5))
* reword description of shift+G: auto playback speed adjustment in readme ([37dff75](https://github.com/exwm/yt_clipper/commit/37dff75e523e78974718d0247dba539bb5cf2c10))
* split change log intwo two for markup script and clipper script ([b9f4c9c](https://github.com/exwm/yt_clipper/commit/b9f4c9c30f65fb175fdc81ebb14b1a2dd5fb14e4))
* Update browser support section and add related scripts section ([35aad3e](https://github.com/exwm/yt_clipper/commit/35aad3ea873ca661c670479d02f8b8503b230f76))
* update changelog for 0.0.63 and add useful youtube controls in readme ([b53ada0](https://github.com/exwm/yt_clipper/commit/b53ada0825c9db459b7dcbd6e6f43796d1970b9a))
* update changelog with all releases to date, including beta and alpha versions ([8fe02a2](https://github.com/exwm/yt_clipper/commit/8fe02a271aa1569cb7f467f2596d91a256c9afba))
* update changelog with markup script 0.0.81 and clipper script 3.5.0 ([f86da85](https://github.com/exwm/yt_clipper/commit/f86da85d48b61245a617b1db18a398bf2089b7a0))
* update feature request template with requirements check boxes ([ac18ed0](https://github.com/exwm/yt_clipper/commit/ac18ed05d33901a6c40ec1b2ddbd173f7490c599))
* update install instructions with v3.0.2 of clipper script ([f3482e5](https://github.com/exwm/yt_clipper/commit/f3482e5fb7417ab0c5b5b575264463aab9d2faaf))
* update project description ([a6da1ee](https://github.com/exwm/yt_clipper/commit/a6da1ee813560526a3f6643e24f0c399fcf3c29b))
* update shortcuts reference with new shortcuts and condense ([adbe2ca](https://github.com/exwm/yt_clipper/commit/adbe2ca3e724c97fdbd818bb68d4588d1d623ed6))

## [5.32.0](https://github.com/exwm/yt_clipper/compare/v5.31.0...v5.32.0) (2025-06-24)


### Features

* **clipper:** add h264_nvenc codec support by @codedealer in ([#60](https://github.com/exwm/yt_clipper/issues/60)) ([588b542](https://github.com/exwm/yt_clipper/commit/588b542a6d494ed8f70c7da9f6472120848f506e))

### Bug Fixes

* **clipper:** h264_vulkan chroma subsampling artifacting and improve compatibility ([ecd5a1f](https://github.com/exwm/yt_clipper/commit/ecd5a1f93ada1dec479f13a0eb7e02d874125e5b))
* **markup:** crop preview should not use rounded corners ([f577df7](https://github.com/exwm/yt_clipper/commit/f577df77e0f967627eb63470784feca162d5f6d0))

## [5.31.0](https://github.com/exwm/yt_clipper/compare/v5.30.0...v5.31.0) (2025-06-03)


### Features

* **markup:** add Ctrl+Alt+X for previewing crop in modal window ([95693d4](https://github.com/exwm/yt_clipper/commit/95693d43ccffb19637d6c42d93287552006de961))


### Bug Fixes

* **clipper:** clip filenames should be escaped from rich formatting ([5fbdd75](https://github.com/exwm/yt_clipper/commit/5fbdd75cbd99d0fb4f138e6dc89454c35a21751f))
* **site:** all video load handlers should be disabled after load ([650d759](https://github.com/exwm/yt_clipper/commit/650d7592812da76f17042ebaa5815eb3311142b1))

## [5.30.0](https://github.com/exwm/yt_clipper/compare/v5.29.0...v5.30.0) (2025-05-10)


### Features

* **markup:** support crop manipulation and drawing when previewing rotation ([bc8a857](https://github.com/exwm/yt_clipper/commit/bc8a85769ad4624991ea916a9b46455945bc4245))


### Bug Fixes

* **markup:generic:** speedchart should appear in front of video ([8774747](https://github.com/exwm/yt_clipper/commit/8774747d7dd7319fc10c1d1cf5a2947b3610768e))


### Documentation Updates

* minor readme and changelog fixes ([8414e0f](https://github.com/exwm/yt_clipper/commit/8414e0f97fa1dd7756773f89b046d7cdffd9a030))

## [5.29.0](https://github.com/exwm/yt_clipper/compare/v5.28.0...v5.29.0) (2025-05-10)


### Features

* **markup+clipper:** support yt_clipper generic video platform (<https://exwm.github.io/yt_clipper/>) ([ea150e3](https://github.com/exwm/yt_clipper/commit/ea150e3a44559e79e3f25093c0a568447617fb1f))
  * If the platform you want to use isn't directly supported, you can download the video manually and then use the yt_clipper generic video platform.
  * Load a video from local storage by dragging and dropping the video onto the player, then activate the yt_clipper markup script as usual.

## [5.28.0](https://github.com/exwm/yt_clipper/compare/v5.27.0...v5.28.0) (2024-10-25)

### Features

* **clipper:** on failure to parse markers JSON file, print friendlier error messages and debug info ([2c7fc9e](https://github.com/exwm/yt_clipper/commit/2c7fc9e07c52e805187942236f299f0870361a69))


### Bug Fixes

* **clipper:** pass --cookiefile option as --cookies to yt-dlp ([0e43f51](https://github.com/exwm/yt_clipper/commit/0e43f5169e62d7ca74361d1f68a308ff4affb1d9)) by @codedealer in ([#54](https://github.com/exwm/yt_clipper/issues/54))
* **clipper:** set yt-dlp location to bundled yt-dlp for frozen releases ([8a80ac1](https://github.com/exwm/yt_clipper/commit/8a80ac133c8ff3ada1950973fe629a0e6e8b98a1))

## [5.27.0](https://github.com/exwm/yt_clipper/compare/v5.26.0...v5.27.0) (2024-10-11)

### Features

* **clipper:** auto update yt-dlp bundled in frozen releases ([5728875](https://github.com/exwm/yt_clipper/commit/57288752081782d5820af26c5f8a98abd4d58217))
* adds option `--no-ytdl-auto-update` to disable automatic updating of bundled yt-dlp
  * adds option `--ytdl-location` to override the location of yt-dlp
  * changes option `--version` to print only yt_clipper's version
  * adds option `--prin-versions` to print versions of yt_clipper and its major dependencies
* **clipper:** use binary yt-dlp to enable updating yt-dlp dep independently ([9316fd4](https://github.com/exwm/yt_clipper/commit/9316fd44480c0d93c2718d4a624fdd988f5e4a5d))
  * removes legacy youtube-dl support which hasn't been updated in several years
* **clipper:** by default, read args from `../yt_clipper_default_args.txt` for frozen releases ([d00d0b6](https://github.com/exwm/yt_clipper/commit/d00d0b647d8b00e55205efd6ec44233269c7b4dc))
* **clipper:** organize options into groups, use rich-argparse for richer help output ([fa7ac45](https://github.com/exwm/yt_clipper/commit/fa7ac45bf13998722bfa56907d312308c653e93a))

## [5.26.0](https://github.com/exwm/yt_clipper/compare/v5.25.0...v5.26.0) (2024-10-09)

### Features

* **clipper:** add --cookiefile option to pass a cookies file to youtube_dl for video platform login ([33bc588](https://github.com/exwm/yt_clipper/commit/33bc5889c02fd293e86ef9230b2e60171b81be34))
  * for more information on passing cookies, see yt-dlp docs: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp
* **clipper:** use rich for richer logging ([e673d24](https://github.com/exwm/yt_clipper/commit/e673d24fbf776659199e9c112de50a13a20031db))
* **clipper:** use yt_clipper icon for python exe builds ([1784a07](https://github.com/exwm/yt_clipper/commit/1784a078a9c2f4378648e18e2ad2609681676c20))

### Major Dependency Upgrades

* **clipper:** update yt-dlp dependency to v2024.10.07 ([d9c8dd5](https://github.com/exwm/yt_clipper/commit/d9c8dd5a88af0f2b93b57a611bfcbc0652e92504))

## [5.25.0](https://github.com/exwm/yt_clipper/compare/v5.24.0...v5.25.0) (2024-09-30)


### Features

* **clipper:** add --video-codec option h264_vulkan for hardware accelerated encodes of h264 ([21a060f](https://github.com/exwm/yt_clipper/commit/21a060fc9cb6e105770b1a93be508d0906040e84))
  * Uses hardware acceleration (typically a discrete GPU) for faster encodes at the cost of some quality.
  * h264_vulkan uses the Vulkan technology which is supported on Linux and Windows across most modern GPUs (AMD/NVIDIA/Intel). MacOS and iOS are not yet supported. Requires ffmpeg >= 7.1.
  * If you have issues with hardware acceleration, ensure you have the latest drivers.
* **clipper:** log audio/video formats found by youtube_dl alternative ([7b93636](https://github.com/exwm/yt_clipper/commit/7b93636ff55364ace18c7559227a4a8f8f229c92))


### Bug Fixes

* **clipper:** crash on --fast-trim with local input video file, updates python from 3.8 to 3.12 ([ff9675e](https://github.com/exwm/yt_clipper/commit/ff9675e860c77aab21806b78284fbcf73384d646))


### Major Dependency Upgrades

* **clipper:** update ffmpeg dependency to 7.1 (supports vulkan encodes) ([a5959da](https://github.com/exwm/yt_clipper/commit/a5959da0c7e8bf0b1dd21e1e32b9420f6a9b2e9c))
* **clipper:** update yt-dlp dependency to v2024.09.27 ([d06bf12](https://github.com/exwm/yt_clipper/commit/d06bf12a9fdb339cf3b02ba36bd1116e5bdde600))

## [5.24.0](https://github.com/exwm/yt_clipper/compare/v5.22.0...v5.24.0) (2024-09-08)


### Features

* **clipper+markup:** add `--enable-hdr` option to use high dynamic range for output videos ([75105af](https://github.com/exwm/yt_clipper/commit/75105afa8b019088b5892cb9496ee787ecd5120b))
  * The option is exposed in the markup script UI in global and marker pair encode settings (opened with **Shift+W**).
  * Typically improves image vibrancy and colors at the expense of file size and playback compatibility.
* **clipper:** add `--fast-trim`/`-ft` option to generate outputs quickly without re-encoding ([3dbf0f4](https://github.com/exwm/yt_clipper/commit/3dbf0f4b9c69a3b0183b2be078e900fbd220af4e))
* **markup:** crop manipulation: allow use of meta key (command on mac) instead of ctrl key ([63ddd76](https://github.com/exwm/yt_clipper/commit/63ddd76f22117ec5d17cf2cd0b20ae43e2ce8b58))
* **clipper:** add --log-level option, fix default log level should be VERBOSE not DEBUG ([a1ee47e](https://github.com/exwm/yt_clipper/commit/a1ee47ec9108f4f7753c506ae9352a60736176d0))


### Bug Fixes

* **clipper:** zoompan: disable scaling up input when input is HDR before zooming to avoid artifacting ([2c5d0e6](https://github.com/exwm/yt_clipper/commit/2c5d0e6ba5d5ce63c0691a64b07b98052bc015ad))
* **markup:** videoURL in markers json missing video ID query param ([fa99571](https://github.com/exwm/yt_clipper/commit/fa99571fc59d395bff3ce8817888f2e62c0f196a))

## [5.22.0](https://github.com/exwm/yt_clipper/compare/v5.21.2...v5.22.0) (2024-08-06)


### Bug Fixes

* **markup:** fix crash when trusted types are required.
  * use DOMPurify for more robust html sanitization, use trusted types with browsers that support it ([85cb724](https://github.com/exwm/yt_clipper/commit/85cb72468054f97ef400b53b2bd51a43389dae14))
  * YouTube on Chrome is rolling out content security policies that require trusted types, see <https://developer.chrome.com/blog/trusted-types-on-youtube>


### Major Dependency Upgrades

* **clipper:** update yt-dlp dependency to v2024.08.06 ([20c80f3](https://github.com/exwm/yt_clipper/commit/20c80f3e12201c6097f354c576b6a3bb1a805888))

## [5.21.2](https://github.com/exwm/yt_clipper/compare/v5.21.1...v5.21.2) (2024-08-04)


### Bug Fixes

* **clipper:** making clips with local input video broken due to missing Video Type ([9a14f4d](https://github.com/exwm/yt_clipper/commit/9a14f4d7266b764ff8f2aeb5decb69c1cbb0daeb))

## [5.21.1](https://github.com/exwm/yt_clipper/compare/v5.21.0...v5.21.1) (2024-08-02)


### Bug Fixes

* **clipper:** work around for video stabilization artifacts when input video has low background contrast ([da31b06](https://github.com/exwm/yt_clipper/commit/da31b0646269bba738fba8de99172d6f2f17b3ce))

## [5.21.0](https://github.com/exwm/yt_clipper/compare/v5.20.0...v5.21.0) (2024-08-02)


### Major Dependency Upgrades

* **clipper:** update yt-dlp dependency from v2024.08.01 ([9781979](https://github.com/exwm/yt_clipper/commit/9781979a168b16c9815c98a8aa8a481906fba06b))

## [5.20.0](https://github.com/exwm/yt_clipper/compare/v5.18.0...v5.20.0) (2024-08-01)


### Features

* **clipper+markup:** add initial support for afreecatv platform vods ([a24b80c](https://github.com/exwm/yt_clipper/commit/a24b80c754763513649b5910307ae8b7c3ae4994))
* **clipper:** enable weverse support ([c9d5c84](https://github.com/exwm/yt_clipper/commit/c9d5c844fae43d67633924141d38c774ef6e2ab6))
* **markup:** support for platform tv.naver.com ([6de0da4](https://github.com/exwm/yt_clipper/commit/6de0da4a11b8ae8046c5cd4a0786dbec6630849d))


### Bug Fixes

* **markup:** marker pair selection via mouseover should work on weverse and naver_tv ([8022ac5](https://github.com/exwm/yt_clipper/commit/8022ac5ba6e72b01e76c679bdb6b17fd0650ff38))

### AfreecaTV Support Notes

* AfreecaTV clips use the hls (http live streaming) protocol which is not as reliable as other protocols.
* Short AfreecaTV clips (about 1 second or shorter) may produce empty video files when.
* AfreecaTV VODs come in multiple video file parts and clips that span multiple parts are not currently supported.

### Major Dependency Upgrades

* **clipper:** update ffmpeg to v7.0.1 ([3c3c534](https://github.com/exwm/yt_clipper/commit/3c3c53456ee2c8a2ce3598e438b22fc19a99480d))

## [5.19.0](https://github.com/exwm/yt_clipper/compare/v5.18.0...v5.19.0) (2024-07-29)


### Features

* **clipper:** enable weverse support ([c9d5c84](https://github.com/exwm/yt_clipper/commit/c9d5c844fae43d67633924141d38c774ef6e2ab6))
* **markup:** support for platform tv.naver.com ([6de0da4](https://github.com/exwm/yt_clipper/commit/6de0da4a11b8ae8046c5cd4a0786dbec6630849d))


### Major Dependency Upgrades

* **clipper:** update ffmpeg to v7.0.1 ([3c3c534](https://github.com/exwm/yt_clipper/commit/3c3c53456ee2c8a2ce3598e438b22fc19a99480d))

## [5.18.0](https://github.com/exwm/yt_clipper/compare/v5.17.0...v5.18.0) (2024-07-29)


### Major Dependency Upgrades

* **clipper:** update yt-dlp dependency from v2024.04.09 to v2024.7.25, update pyinstaller from v5.0.1 to v6.9.0 ([a2defb9](https://github.com/exwm/yt_clipper/commit/a2defb927e6cd21fe14cc6e97aefa096ffc148e9))

## [5.17.0](https://github.com/exwm/yt_clipper/compare/v5.16.1...v5.17.0) (2024-04-18)


### Major Dependency Upgrades

* **clipper:** update yt-dlp dependency from v2023.11.16 to v2024.04.09 ([f8a5924](https://github.com/exwm/yt_clipper/commit/f8a592469b6505ee43b3d3e3af7bf3e87c72f359))

### [5.16.1](https://github.com/exwm/yt_clipper/compare/v5.16.0...v5.16.1) (2023-12-08)


### Features

* **clipper/h264:** add --h264-disable-reduce-stutter/--h264-drs flag for opting in to a consistent framerate with duplicate frames when slowing down clips for potentially smoother merged video transitions ([55beecc](https://github.com/exwm/yt_clipper/commit/55beecc52a4ce6c0542a3b19e6c983c7f6c510e9))


### Bug Fixes

* **clipper/h264:** add consistent timescale to reduce hanging when merging clips ([352fc46](https://github.com/exwm/yt_clipper/commit/352fc46a725c8ea951c2100bc6a31f0c6d879def))

## [5.16.0](https://github.com/exwm/yt_clipper/compare/v5.15.0...v5.16.0) (2023-12-06)


### Features

* **platform:** add support for naver_now_watch platform (now.naver.com/watch URLs) ([c77d8a0](https://github.com/exwm/yt_clipper/commit/c77d8a0ca67f3cd121d19548812ae134c969b035))

## [5.15.0](https://github.com/exwm/yt_clipper/compare/v5.14.2...v5.15.0) (2023-11-20)


### Major Dependency Upgrades

* **clipper:** update ffmpeg to v6.1 ([7ce2052](https://github.com/exwm/yt_clipper/commit/7ce2052ec1ded09a8f1eec9397287a9ae843f2e8))
* **clipper:** update yt-dlp dependency from v2023.07.06 to v2023.11.16 ([ccb017a](https://github.com/exwm/yt_clipper/commit/ccb017a45864e28170f68bf024f7fabc6b77c6a0))

### [5.14.2](https://github.com/exwm/yt_clipper/compare/v5.14.1...v5.14.2) (2023-08-23)


### Bug Fixes

* **markup:** marker pair and global settings editors covering up video player ([0e9f06d](https://github.com/exwm/yt_clipper/commit/0e9f06d46d7bfde8df72ac9f0bdc0c7ed45c15a9))

### [5.14.1](https://github.com/exwm/yt_clipper/compare/v5.14.0...v5.14.1) (2023-08-19)


### Bug Fixes

* **clipper:** 0-duration crop point pair at the end of dynamic crop map breaks crop filter ([731d3ab](https://github.com/exwm/yt_clipper/commit/731d3ab9956d5aa7b4cb3254e9e038d834a459da))
* **clipper:** video stabilization fails due to ffmpeg bug ([9255893](https://github.com/exwm/yt_clipper/commit/92558936f57bfaa51dd1ec18ba8835986ccca143))
* **markup:** marker pair and global settings editors not displaying, rotate video doesn't fit video into view properly, settings editors invisible in non-theatre view mode ([8a2a458](https://github.com/exwm/yt_clipper/commit/8a2a458c5dcc10cc6a8a98bbdbe9fc724f1175a5))

## [5.14.0](https://github.com/exwm/yt_clipper/compare/v5.12.0...v5.14.0) (2023-08-12)


### Features

* **clipper:** change default --format-sort option for yt-dlp to prefer premium bitrate formats ([7ab962b](https://github.com/exwm/yt_clipper/commit/7ab962b3a105b196d0ba45500333e0eb9c6530bc))


### Bug Fixes

* **clipper:** add warning and prompt to disable potentially unsupported video download protocols m3u8/m3u8_native ([932368e](https://github.com/exwm/yt_clipper/commit/932368eec74ad6872d8eebb8b79c4dbb7bd49fbf))
* **clipper:** fix ValueError exception with python>=3.11 from ClipperState dataclass decorator ([dc9c937](https://github.com/exwm/yt_clipper/commit/dc9c9375516da7f0393ad46b1d5714493c157856))
* **clipper:** use -fps_mode vfr to fix encoding hang with variable speed mode, add output frameout options for h264 to reduce stutter when video is slowed ([ae3c172](https://github.com/exwm/yt_clipper/commit/ae3c17280dfa8997a68f1d547c1e61afbf75d4a0))
* **markup:** marker pair and global settings editors not displaying, rotate video doesn't fit video into view properly ([3abb89d](https://github.com/exwm/yt_clipper/commit/3abb89d6569acd4fccf1a914c33ef4440a9befad))
* **markup:** marker pair and global settings editors, flash messages (toasts), shortcuts table not injected just below video ([3edb00e](https://github.com/exwm/yt_clipper/commit/3edb00ebc26f6f6bd70019716faec44b883d7f44))
* **markup:** video progress bar and markers should be interactable when speed chart is displaying ([840f078](https://github.com/exwm/yt_clipper/commit/840f07862570f8dc3e3d7bbb5035f360692ff291))


### Major Dependency Upgrades

* **clipper:** update yt-dlp dependency from v2023.03.03 to v2023.07.06 ([69c0b34](https://github.com/exwm/yt_clipper/commit/69c0b3417693bcb9a067045cf0ade8f10e51e2e0))
* **clipper:** ffmpeg dependency updated to v6.0.0 (latest master branch builds)
