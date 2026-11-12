import argparse
import sys
from pathlib import Path

from .PDFgenerator import PDFGenerator


def save_all(gen:PDFGenerator, args:argparse.Namespace, parser:argparse.ArgumentParser):
    groups = gen.items.groupby("Supplier Name", sort=True)
    if args.vendors:
        wanted = set(args.vendors)
        groups = [(n, g) for n, g in groups if n in wanted]
        missing = wanted - {n for n, _ in groups}
        if missing:
            parser.error(f"vendor(s) not found: {', '.join(sorted(missing))}")

    count = 0
    for name, grp in groups:
        if args.dry_run:
            print(f"{name}: {len(grp)} line item(s)")
            continue
        gen.save_pdf(name, grp)
        count += 1
        if not args.quiet:
            print(f"wrote PDF for {name} ({len(grp)} line item(s))")

    gen.save_excel()
    print(f"wrote EXCEL file for {len(gen.items)} line item(s)")
    count += 1

    if not args.dry_run and not args.quiet:
        print(f"{count} file(s) written to {args.outdir}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate filled purchase order PDFs from a requisition HTML export.",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=Path.cwd() / "Oracle iProcurement_ Requisitions.html",
        help="Path to the requisition HTML file. (default: Oracle iProcurement_ Requisitions.html in current directory)",
    )
    parser.add_argument(
        "-t", "--template",
        type=Path,
        default=Path.cwd() / "Purchase Order Request Form.pdf",
        help="Path to the blank PORF PDF template. (default: Purchase Order Request Form.pdf in current directory)",
    )
    parser.add_argument(
        "-o", "--outdir",
        type=Path,
        default=Path.cwd(),
        help="Directory to write generated PDFs into (default: current directory).",
    )
    parser.add_argument(
        "-v", "--vendor",
        action="append",
        dest="vendors",
        metavar="NAME",
        help="Only generate for this vendor; repeatable. Default: all vendors.",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="List vendors and line counts without writing PDFs.",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress per-file output.",
    )

    args = parser.parse_args(argv)

    for path, label in ((args.html, "HTML file"), (args.template, "template")):
        if not path.is_file():
            parser.error(f"{label} not found: {path}")

    args.outdir.mkdir(parents=True, exist_ok=True)

    gen = PDFGenerator(args.html, args.template)

    save_all(gen, args, parser)

    return 0


if __name__ == "__main__":
    sys.exit(main())
