# Changelog

## [0.1.1](https://github.com/mortenkrane/dokken/compare/dokken-v0.1.0...dokken-v0.1.1) (2026-01-06)


### Features

* add /lint-test slash command for comprehensive quality checks ([#88](https://github.com/mortenkrane/dokken/issues/88)) ([a5f1338](https://github.com/mortenkrane/dokken/commit/a5f133821bbc60b3c6dab4dd646257a2cb14a3f3))
* add auto-merge workflow for Renovate PRs ([#41](https://github.com/mortenkrane/dokken/issues/41)) ([4d14379](https://github.com/mortenkrane/dokken/commit/4d143798c166c186b4846986efbcd78cf204d2cc))
* add butterfly diagram support for control flow ([#33](https://github.com/mortenkrane/dokken/issues/33)) ([85ced63](https://github.com/mortenkrane/dokken/commit/85ced63560350ef3c5cdfbe04e20ef21d8834a88))
* add configurable file types for multi-language support ([#85](https://github.com/mortenkrane/dokken/issues/85)) ([46f17b1](https://github.com/mortenkrane/dokken/commit/46f17b1cd81320d45e298b583c3f1ec837d08869))
* Add Makefile for consolidated development workflow ([#18](https://github.com/mortenkrane/dokken/issues/18)) ([9920861](https://github.com/mortenkrane/dokken/commit/9920861e5e252386e11ec56117d3d98fff8ee994))
* add prompt injection mitigation with XML delimiters and validation ([#98](https://github.com/mortenkrane/dokken/issues/98)) ([100819f](https://github.com/mortenkrane/dokken/commit/100819f1f9c1e68625f0419e927daa52e9cc3553))
* add Python 3.10-3.13 support with parallel CI testing ([#83](https://github.com/mortenkrane/dokken/issues/83)) ([0c22316](https://github.com/mortenkrane/dokken/commit/0c22316b993f6afe6df156fa5ccedc4be36d61f2))
* Add release-please for automated releases and PyPI publishing ([#8](https://github.com/mortenkrane/dokken/issues/8)) ([e51f45b](https://github.com/mortenkrane/dokken/commit/e51f45b3669cdd58a1158c434a3e25e4ac492aab))
* add TypedDict for config type safety ([#69](https://github.com/mortenkrane/dokken/issues/69)) ([fd26550](https://github.com/mortenkrane/dokken/commit/fd26550004a9788d7584ba459a662ef7acd7abcb))
* cache drift detection to reduce llm usage and improve performance ([#55](https://github.com/mortenkrane/dokken/issues/55)) ([f83028d](https://github.com/mortenkrane/dokken/commit/f83028d0266f749510af35bfe35ec5b9debb32c6))
* custom prompts ([#47](https://github.com/mortenkrane/dokken/issues/47)) ([4d20579](https://github.com/mortenkrane/dokken/commit/4d205796a82c51b6126ea0d0bfb17f787d34113f))
* enable ruff PLC0415 rule and fix inline imports ([#90](https://github.com/mortenkrane/dokken/issues/90)) ([feb321e](https://github.com/mortenkrane/dokken/commit/feb321e22a9c4c5645a0205d00ed37997dd1916c))
* human-in-the-loop ([#21](https://github.com/mortenkrane/dokken/issues/21)) ([463fcfd](https://github.com/mortenkrane/dokken/commit/463fcfd69a8b34443acf5e1a9d736ca45bfe9118))
* improve drift detection for mixed philosophy/technical docs ([#92](https://github.com/mortenkrane/dokken/issues/92)) ([720190c](https://github.com/mortenkrane/dokken/commit/720190cf24461478776d2f1b77be7794cd8b0adc))
* multi-module drift detection ([#48](https://github.com/mortenkrane/dokken/issues/48)) ([22a8762](https://github.com/mortenkrane/dokken/commit/22a8762766b8b0387d397d5b7dda0f516bdb3384))
* parallelize file reading in code analyzer ([#73](https://github.com/mortenkrane/dokken/issues/73)) ([b674768](https://github.com/mortenkrane/dokken/commit/b6747689e67d588a9c307659b0fb01d1f2d8a098))
* Persistent drift cache ([#78](https://github.com/mortenkrane/dokken/issues/78)) ([5efa747](https://github.com/mortenkrane/dokken/commit/5efa747b56e4fe8680abab48be3236686ff6078f))
* pipe drift detection rationale into generation process ([#46](https://github.com/mortenkrane/dokken/issues/46)) ([c2cc29d](https://github.com/mortenkrane/dokken/commit/c2cc29d49e2855fa60536dcbfca082804cc08934))
* Refine documentation generation for better developer focus ([#20](https://github.com/mortenkrane/dokken/issues/20)) ([eddb12d](https://github.com/mortenkrane/dokken/commit/eddb12d09d6462bd0f844ac0e5859ed335ef8969))
* searchable and scannable docs, optimized for agent usage ([#49](https://github.com/mortenkrane/dokken/issues/49)) ([b985254](https://github.com/mortenkrane/dokken/commit/b9852549c603314680ee1fa6e1645c5712f1bc63))
* stabilize doc drift detection ([#82](https://github.com/mortenkrane/dokken/issues/82)) ([8cd61c7](https://github.com/mortenkrane/dokken/commit/8cd61c74c10190c669651e83cc297f69e1c6f682))
* Support for multiple doc types ([#24](https://github.com/mortenkrane/dokken/issues/24)) ([30ebd61](https://github.com/mortenkrane/dokken/commit/30ebd61c3e9d214031cec17b7f7130642906220b))


### Bug Fixes

* add type assertions for CI type checks ([#30](https://github.com/mortenkrane/dokken/issues/30)) ([66cd868](https://github.com/mortenkrane/dokken/commit/66cd868e7ad0c870946e7896391805b02549e8ce))
* correct mock_console fixture to patch actual console locations ([#65](https://github.com/mortenkrane/dokken/issues/65)) ([c609722](https://github.com/mortenkrane/dokken/commit/c60972297ad43e0d53ee3d2439bea5f249d9e84a))
* correct Python version and configure ty for CI ([#19](https://github.com/mortenkrane/dokken/issues/19)) ([444cf74](https://github.com/mortenkrane/dokken/commit/444cf74b66949ee3fa2299b75fc6de768de13588))
* **deps:** update all non-major dependencies ([#10](https://github.com/mortenkrane/dokken/issues/10)) ([86f709c](https://github.com/mortenkrane/dokken/commit/86f709c581f26445f312717025ed315e0b3b8cdc))
* **deps:** update all non-major dependencies ([#43](https://github.com/mortenkrane/dokken/issues/43)) ([52d3f9e](https://github.com/mortenkrane/dokken/commit/52d3f9e76799b025572c80942cd6f922ec169a0a))
* **deps:** update all non-major dependencies ([#96](https://github.com/mortenkrane/dokken/issues/96)) ([1c38d1a](https://github.com/mortenkrane/dokken/commit/1c38d1ae664a0ba9e7159ab124bb705af6f5c35e))
* dev dependencies ([#45](https://github.com/mortenkrane/dokken/issues/45)) ([085537b](https://github.com/mortenkrane/dokken/commit/085537bfb0b68330c89d709399e73ce3eec034a8))
* improve drift detection for incomplete module structure ([#100](https://github.com/mortenkrane/dokken/issues/100)) ([0bf4291](https://github.com/mortenkrane/dokken/commit/0bf4291b3d7f8c7b3e0bc18952e81b3902d82c7a))
* make drift checker focus on important architectural changes only ([#86](https://github.com/mortenkrane/dokken/issues/86)) ([ae3e78b](https://github.com/mortenkrane/dokken/commit/ae3e78b72384f0fcfa7d8b9a9f972b0f66e52389))
* resolve ruff E501 line length violations in tests ([#53](https://github.com/mortenkrane/dokken/issues/53)) ([f03821d](https://github.com/mortenkrane/dokken/commit/f03821d4fa289fe938d3090d4e90f78bdd1c9223))
* simplify mdformat CI command to use current directory ([#34](https://github.com/mortenkrane/dokken/issues/34)) ([425872a](https://github.com/mortenkrane/dokken/commit/425872a4b0f370aa01f7651d6bd2a720d316e178))


### Documentation

* add code review agent specification ([#81](https://github.com/mortenkrane/dokken/issues/81)) ([020629e](https://github.com/mortenkrane/dokken/commit/020629e7780d45b2e60cbde316c68c59398d534a))
* add type annotations to all code examples in style guide ([#29](https://github.com/mortenkrane/dokken/issues/29)) ([cd6c054](https://github.com/mortenkrane/dokken/commit/cd6c054ba11eda66bda9654dca0a466b77d4909d))
* comprehensive architecture and code quality review ([#61](https://github.com/mortenkrane/dokken/issues/61)) ([03e38a9](https://github.com/mortenkrane/dokken/commit/03e38a9079d84f396384243f08bdc3da990e9d77))
* comprehensive repository review and future improvements update ([#99](https://github.com/mortenkrane/dokken/issues/99)) ([b3bffa2](https://github.com/mortenkrane/dokken/commit/b3bffa2c5d89e131a7d5ac8cfe4f51cbac925dac))
* consolidate documentation across README, style-guide, and CLAUDE.md ([#9](https://github.com/mortenkrane/dokken/issues/9)) ([9036fc7](https://github.com/mortenkrane/dokken/commit/9036fc7c6a39b97b301a697e79c5cd8136cbeef6))
* emphasize human questionnaire and grep-optimized output in intro ([#91](https://github.com/mortenkrane/dokken/issues/91)) ([578aadd](https://github.com/mortenkrane/dokken/commit/578aadd1c9ebac41d00464f5c93de93640a65698))
* extract contributing guidelines to CONTRIBUTING.md ([#38](https://github.com/mortenkrane/dokken/issues/38)) ([0bc9ef4](https://github.com/mortenkrane/dokken/commit/0bc9ef42eb615cfb91db3328c475e8b128ea133f))
* generate module README for src directory ([#95](https://github.com/mortenkrane/dokken/issues/95)) ([b41e9ce](https://github.com/mortenkrane/dokken/commit/b41e9ce3a2b346c351d5c84e8fdcfc37e6f868db))
* review code base ([#76](https://github.com/mortenkrane/dokken/issues/76)) ([270866b](https://github.com/mortenkrane/dokken/commit/270866b48a8cda8fae6a41730a6cc643f70fe5b2))
* revise README for accuracy and completeness ([#74](https://github.com/mortenkrane/dokken/issues/74)) ([b9a5a27](https://github.com/mortenkrane/dokken/commit/b9a5a27b5f4089f7196896c567925ba09e698130))
* streamline CLAUDE.md and make pre-commit requirements explicit ([#93](https://github.com/mortenkrane/dokken/issues/93)) ([426df55](https://github.com/mortenkrane/dokken/commit/426df55e0242dd08360419fd17e1866f04f10319))
* update src module documentation with missing components ([#101](https://github.com/mortenkrane/dokken/issues/101)) ([afbfefc](https://github.com/mortenkrane/dokken/commit/afbfefcf1951095514b49fcbb864b7e96754b17b))
* update style guide to match current codebase ([#22](https://github.com/mortenkrane/dokken/issues/22)) ([a52cff9](https://github.com/mortenkrane/dokken/commit/a52cff9ebd0490f3961b8796adc50f943eba78a7))


### Code Refactoring

* centralize error messages and constants ([#71](https://github.com/mortenkrane/dokken/issues/71)) ([dcde9b2](https://github.com/mortenkrane/dokken/commit/dcde9b25555a1bbbd76048415718a797bdbdff4c))
* clean up multi-doc-type implementation ([#31](https://github.com/mortenkrane/dokken/issues/31)) ([afb10ee](https://github.com/mortenkrane/dokken/commit/afb10ee92328a5eb8a4b41c789fcbad912c715d7))
* extract common workflow initialization logic ([#66](https://github.com/mortenkrane/dokken/issues/66)) ([4415fe3](https://github.com/mortenkrane/dokken/commit/4415fe30092b13b2e67ac53cac1832a526c73ca1))
* extract helper functions from check_multiple_modules_drift ([#64](https://github.com/mortenkrane/dokken/issues/64)) ([663c241](https://github.com/mortenkrane/dokken/commit/663c241f5398ae7d333936a32957e3f57d3c6135))
* extract prompt assembly logic from llm.py ([#2](https://github.com/mortenkrane/dokken/issues/2)) ([#63](https://github.com/mortenkrane/dokken/issues/63)) ([db2ccf2](https://github.com/mortenkrane/dokken/commit/db2ccf27bd5f9a9d1b6240f80a393292458c1436))
* improve code, add doc with future improvements ideas ([#35](https://github.com/mortenkrane/dokken/issues/35)) ([e973959](https://github.com/mortenkrane/dokken/commit/e9739595bc10d84be9bd0d4726cf0f4d615a3a20))
* move DocumentationContext to records.py ([#70](https://github.com/mortenkrane/dokken/issues/70)) ([cbe5182](https://github.com/mortenkrane/dokken/commit/cbe51825e24991276daf5b54cde7ebbf34b3611c))
* move LLM-related files into llm submodule ([#94](https://github.com/mortenkrane/dokken/issues/94)) ([6f58308](https://github.com/mortenkrane/dokken/commit/6f583089b5382408e9cfe8cb2bf662a62c4d6cd3))
* move tests from src/tests/ to tests/ ([#50](https://github.com/mortenkrane/dokken/issues/50)) ([ccb5300](https://github.com/mortenkrane/dokken/commit/ccb5300c812ecb2805e49597deaea986df30eaae))
* remove symbol exclusion filtering support ([#102](https://github.com/mortenkrane/dokken/issues/102)) ([2cf2c42](https://github.com/mortenkrane/dokken/commit/2cf2c429b2aad77f860182b03e2b5485f393bc58))
* replace NO_DOC_MARKER with Optional pattern ([#72](https://github.com/mortenkrane/dokken/issues/72)) ([b0fffa8](https://github.com/mortenkrane/dokken/commit/b0fffa8474edc75c9a322625ba7b05901795eef0))
* simplify documentation prompts to focus on high-level concepts ([#87](https://github.com/mortenkrane/dokken/issues/87)) ([88e4168](https://github.com/mortenkrane/dokken/commit/88e416803d43ced4ff63cf6bc8e3aa17b803724b))
* split config module into separate concerns ([#60](https://github.com/mortenkrane/dokken/issues/60)) ([c8e80a3](https://github.com/mortenkrane/dokken/commit/c8e80a3c587d24702ce252c5aed52e9e381a05e6))
* split utils.py into focused modules for SRP compliance ([#62](https://github.com/mortenkrane/dokken/issues/62)) ([381b176](https://github.com/mortenkrane/dokken/commit/381b176681b8bdd4b4ab46cb584bd72c33d85501))
