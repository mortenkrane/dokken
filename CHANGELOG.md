# Changelog

## [0.1.1](https://github.com/mortenkrane/dokken/compare/dokken-v0.1.0...dokken-v0.1.1) (2025-12-27)


### Features

* add auto-merge workflow for Renovate PRs ([#41](https://github.com/mortenkrane/dokken/issues/41)) ([4d14379](https://github.com/mortenkrane/dokken/commit/4d143798c166c186b4846986efbcd78cf204d2cc))
* add butterfly diagram support for control flow ([#33](https://github.com/mortenkrane/dokken/issues/33)) ([85ced63](https://github.com/mortenkrane/dokken/commit/85ced63560350ef3c5cdfbe04e20ef21d8834a88))
* Add Makefile for consolidated development workflow ([#18](https://github.com/mortenkrane/dokken/issues/18)) ([9920861](https://github.com/mortenkrane/dokken/commit/9920861e5e252386e11ec56117d3d98fff8ee994))
* Add release-please for automated releases and PyPI publishing ([#8](https://github.com/mortenkrane/dokken/issues/8)) ([e51f45b](https://github.com/mortenkrane/dokken/commit/e51f45b3669cdd58a1158c434a3e25e4ac492aab))
* add TypedDict for config type safety ([#69](https://github.com/mortenkrane/dokken/issues/69)) ([fd26550](https://github.com/mortenkrane/dokken/commit/fd26550004a9788d7584ba459a662ef7acd7abcb))
* cache drift detection to reduce llm usage and improve performance ([#55](https://github.com/mortenkrane/dokken/issues/55)) ([f83028d](https://github.com/mortenkrane/dokken/commit/f83028d0266f749510af35bfe35ec5b9debb32c6))
* custom prompts ([#47](https://github.com/mortenkrane/dokken/issues/47)) ([4d20579](https://github.com/mortenkrane/dokken/commit/4d205796a82c51b6126ea0d0bfb17f787d34113f))
* human-in-the-loop ([#21](https://github.com/mortenkrane/dokken/issues/21)) ([463fcfd](https://github.com/mortenkrane/dokken/commit/463fcfd69a8b34443acf5e1a9d736ca45bfe9118))
* multi-module drift detection ([#48](https://github.com/mortenkrane/dokken/issues/48)) ([22a8762](https://github.com/mortenkrane/dokken/commit/22a8762766b8b0387d397d5b7dda0f516bdb3384))
* parallelize file reading in code analyzer ([#73](https://github.com/mortenkrane/dokken/issues/73)) ([b674768](https://github.com/mortenkrane/dokken/commit/b6747689e67d588a9c307659b0fb01d1f2d8a098))
* pipe drift detection rationale into generation process ([#46](https://github.com/mortenkrane/dokken/issues/46)) ([c2cc29d](https://github.com/mortenkrane/dokken/commit/c2cc29d49e2855fa60536dcbfca082804cc08934))
* Refine documentation generation for better developer focus ([#20](https://github.com/mortenkrane/dokken/issues/20)) ([eddb12d](https://github.com/mortenkrane/dokken/commit/eddb12d09d6462bd0f844ac0e5859ed335ef8969))
* searchable and scannable docs, optimized for agent usage ([#49](https://github.com/mortenkrane/dokken/issues/49)) ([b985254](https://github.com/mortenkrane/dokken/commit/b9852549c603314680ee1fa6e1645c5712f1bc63))
* Support for multiple doc types ([#24](https://github.com/mortenkrane/dokken/issues/24)) ([30ebd61](https://github.com/mortenkrane/dokken/commit/30ebd61c3e9d214031cec17b7f7130642906220b))


### Bug Fixes

* add type assertions for CI type checks ([#30](https://github.com/mortenkrane/dokken/issues/30)) ([66cd868](https://github.com/mortenkrane/dokken/commit/66cd868e7ad0c870946e7896391805b02549e8ce))
* correct mock_console fixture to patch actual console locations ([#65](https://github.com/mortenkrane/dokken/issues/65)) ([c609722](https://github.com/mortenkrane/dokken/commit/c60972297ad43e0d53ee3d2439bea5f249d9e84a))
* correct Python version and configure ty for CI ([#19](https://github.com/mortenkrane/dokken/issues/19)) ([444cf74](https://github.com/mortenkrane/dokken/commit/444cf74b66949ee3fa2299b75fc6de768de13588))
* **deps:** update all non-major dependencies ([#10](https://github.com/mortenkrane/dokken/issues/10)) ([86f709c](https://github.com/mortenkrane/dokken/commit/86f709c581f26445f312717025ed315e0b3b8cdc))
* dev dependencies ([#45](https://github.com/mortenkrane/dokken/issues/45)) ([085537b](https://github.com/mortenkrane/dokken/commit/085537bfb0b68330c89d709399e73ce3eec034a8))
* resolve ruff E501 line length violations in tests ([#53](https://github.com/mortenkrane/dokken/issues/53)) ([f03821d](https://github.com/mortenkrane/dokken/commit/f03821d4fa289fe938d3090d4e90f78bdd1c9223))
* simplify mdformat CI command to use current directory ([#34](https://github.com/mortenkrane/dokken/issues/34)) ([425872a](https://github.com/mortenkrane/dokken/commit/425872a4b0f370aa01f7651d6bd2a720d316e178))


### Documentation

* add type annotations to all code examples in style guide ([#29](https://github.com/mortenkrane/dokken/issues/29)) ([cd6c054](https://github.com/mortenkrane/dokken/commit/cd6c054ba11eda66bda9654dca0a466b77d4909d))
* comprehensive architecture and code quality review ([#61](https://github.com/mortenkrane/dokken/issues/61)) ([03e38a9](https://github.com/mortenkrane/dokken/commit/03e38a9079d84f396384243f08bdc3da990e9d77))
* consolidate documentation across README, style-guide, and CLAUDE.md ([#9](https://github.com/mortenkrane/dokken/issues/9)) ([9036fc7](https://github.com/mortenkrane/dokken/commit/9036fc7c6a39b97b301a697e79c5cd8136cbeef6))
* extract contributing guidelines to CONTRIBUTING.md ([#38](https://github.com/mortenkrane/dokken/issues/38)) ([0bc9ef4](https://github.com/mortenkrane/dokken/commit/0bc9ef42eb615cfb91db3328c475e8b128ea133f))
* revise README for accuracy and completeness ([#74](https://github.com/mortenkrane/dokken/issues/74)) ([b9a5a27](https://github.com/mortenkrane/dokken/commit/b9a5a27b5f4089f7196896c567925ba09e698130))
* update style guide to match current codebase ([#22](https://github.com/mortenkrane/dokken/issues/22)) ([a52cff9](https://github.com/mortenkrane/dokken/commit/a52cff9ebd0490f3961b8796adc50f943eba78a7))


### Code Refactoring

* centralize error messages and constants ([#71](https://github.com/mortenkrane/dokken/issues/71)) ([dcde9b2](https://github.com/mortenkrane/dokken/commit/dcde9b25555a1bbbd76048415718a797bdbdff4c))
* clean up multi-doc-type implementation ([#31](https://github.com/mortenkrane/dokken/issues/31)) ([afb10ee](https://github.com/mortenkrane/dokken/commit/afb10ee92328a5eb8a4b41c789fcbad912c715d7))
* extract common workflow initialization logic ([#66](https://github.com/mortenkrane/dokken/issues/66)) ([4415fe3](https://github.com/mortenkrane/dokken/commit/4415fe30092b13b2e67ac53cac1832a526c73ca1))
* extract helper functions from check_multiple_modules_drift ([#64](https://github.com/mortenkrane/dokken/issues/64)) ([663c241](https://github.com/mortenkrane/dokken/commit/663c241f5398ae7d333936a32957e3f57d3c6135))
* extract prompt assembly logic from llm.py ([#2](https://github.com/mortenkrane/dokken/issues/2)) ([#63](https://github.com/mortenkrane/dokken/issues/63)) ([db2ccf2](https://github.com/mortenkrane/dokken/commit/db2ccf27bd5f9a9d1b6240f80a393292458c1436))
* improve code, add doc with future improvements ideas ([#35](https://github.com/mortenkrane/dokken/issues/35)) ([e973959](https://github.com/mortenkrane/dokken/commit/e9739595bc10d84be9bd0d4726cf0f4d615a3a20))
* move DocumentationContext to records.py ([#70](https://github.com/mortenkrane/dokken/issues/70)) ([cbe5182](https://github.com/mortenkrane/dokken/commit/cbe51825e24991276daf5b54cde7ebbf34b3611c))
* move tests from src/tests/ to tests/ ([#50](https://github.com/mortenkrane/dokken/issues/50)) ([ccb5300](https://github.com/mortenkrane/dokken/commit/ccb5300c812ecb2805e49597deaea986df30eaae))
* replace NO_DOC_MARKER with Optional pattern ([#72](https://github.com/mortenkrane/dokken/issues/72)) ([b0fffa8](https://github.com/mortenkrane/dokken/commit/b0fffa8474edc75c9a322625ba7b05901795eef0))
* split config module into separate concerns ([#60](https://github.com/mortenkrane/dokken/issues/60)) ([c8e80a3](https://github.com/mortenkrane/dokken/commit/c8e80a3c587d24702ce252c5aed52e9e381a05e6))
* split utils.py into focused modules for SRP compliance ([#62](https://github.com/mortenkrane/dokken/issues/62)) ([381b176](https://github.com/mortenkrane/dokken/commit/381b176681b8bdd4b4ab46cb584bd72c33d85501))
