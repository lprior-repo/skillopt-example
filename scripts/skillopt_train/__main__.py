from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ci_runner import main as ci_main
from .diff_report import main as diff_main
from .leaderboard import main as lb_main
from .skill_train import main as skill_train_main
from .train_loop import main as train_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillopt_train", description="AI-native Holzman SkillOpt training loop"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_train = sub.add_parser("train", help="Run the propose->grade->keep_best loop")
    p_train.add_argument("--config", required=True, help="Path to skillopt-train config JSON")
    p_train.add_argument("--resume", action="store_true", help="Resume from latest checkpoint")

    p_ci = sub.add_parser("ci", help="Run one optimization step for CI/cron")
    p_ci.add_argument("--config", required=True)
    p_ci.add_argument("--budget-json", default="", help="Optional path to read budget state from")

    p_lb = sub.add_parser("leaderboard", help="Query the leaderboard")
    p_lb.add_argument("--store", required=True)
    p_lb.add_argument("--best", action="store_true", help="Print the best entry as JSON")
    p_lb.add_argument("--limit", type=int, default=10)
    p_lb.add_argument("--candidate", default="", help="Filter by candidate name")

    p_diff = sub.add_parser("diff", help="Diff two eval runs")
    p_diff.add_argument("--before", required=True, help="Path to before summary.json")
    p_diff.add_argument("--after", required=True, help="Path to after summary.json")
    p_diff.add_argument("--out", default="", help="Optional path to write markdown report")

    p_run = sub.add_parser("run", help="Run the loop for a specific skill by name")
    p_run.add_argument("skill_name", help="Skill name (directory under skills/)")
    p_run.add_argument("--skills-root", default="skills", help="Path to the skills/ directory")
    p_run.add_argument(
        "--data-root",
        default="data",
        help="Path to data/ for runs, leaderboard, budget, state",
    )
    p_run.add_argument(
        "--provider",
        default="mock:dryrun",
        help="LLM provider spec (e.g. anthropic:claude-sonnet-4-5)",
    )
    p_run.add_argument("--model", default="", help="Model passed to the eval")
    p_run.add_argument("--steps", type=int, default=4)
    p_run.add_argument("--resume", action="store_true", help="Resume from saved state")

    p_list = sub.add_parser("list", help="List all discoverable skills")
    p_list.add_argument("--skills-root", default="skills", help="Path to the skills/ directory")

    return parser


def dispatch(argv: tuple[str, ...]) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv))
    match args.command:
        case "train":
            return train_main(Path(args.config).expanduser(), bool(args.resume))
        case "ci":
            budget_path = (
                Path(args.budget_json).expanduser() if args.budget_json else None
            )
            return ci_main(Path(args.config).expanduser(), budget_path)
        case "leaderboard":
            print(
                lb_main(
                    Path(args.store).expanduser(),
                    bool(args.best),
                    int(args.limit),
                    str(args.candidate),
                )
            )
            return 0
        case "diff":
            out_path = Path(args.out).expanduser() if args.out else None
            return diff_main(
                Path(args.before).expanduser(),
                Path(args.after).expanduser(),
                out_path,
            )
        case "run":
            from .skill import Skill

            skills_root = Path(args.skills_root).expanduser()
            skill = Skill.find(skills_root, args.skill_name)
            data_root = Path(args.data_root).expanduser()
            return skill_train_main(
                skill=skill,
                data_root=data_root,
                provider_spec=str(args.provider),
                resume=bool(args.resume),
                max_steps=int(args.steps),
            )
        case "list":
            from .skill import Skill

            skills_root = Path(args.skills_root).expanduser()
            for skill in Skill.discover(skills_root):
                print(f"{skill.name}\t{skill.path}")
            return 0
        case _:
            parser.print_help(sys.stderr)
            return 2


def main() -> int:
    return dispatch(tuple(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
