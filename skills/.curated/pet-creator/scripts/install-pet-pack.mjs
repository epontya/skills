#!/usr/bin/env node

import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const PACK_ID_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const PNG_EXTENSION = ".png";
const REQUIRED_STATES = ["idle", "working", "needsUserInput", "ready"];
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

async function main() {
  const args = process.argv.slice(2);
  const validateOnly = args[0] === "--validate-only";
  const sourceDir = validateOnly ? args[1] : args[0];
  if (!sourceDir) {
    throw new Error(
      "Usage: node install-pet-pack.mjs [--validate-only] /absolute/path/to/pack",
    );
  }

  const resolvedSourceDir = path.resolve(sourceDir);
  const manifest = await readManifest(resolvedSourceDir);
  validateManifest(manifest);

  const resolvedThumbnailPath = resolvePackPath(
    resolvedSourceDir,
    manifest.thumbnail,
  );
  const thumbnailStats = await fs.stat(resolvedThumbnailPath);
  if (!thumbnailStats.isFile()) {
    throw new Error(`Asset is not a file: ${manifest.thumbnail}`);
  }
  if (path.extname(resolvedThumbnailPath).toLowerCase() !== PNG_EXTENSION) {
    throw new Error(`Thumbnail must be a PNG file: ${manifest.thumbnail}`);
  }
  await readPngSize(resolvedThumbnailPath);

  await Promise.all(
    REQUIRED_STATES.map(async (state) => {
      const stateConfig = manifest.states[state];
      const relativeAssetPath = stateConfig.path;
      const resolvedAssetPath = resolvePackPath(
        resolvedSourceDir,
        relativeAssetPath,
      );
      const stats = await fs.stat(resolvedAssetPath);
      if (!stats.isFile()) {
        throw new Error(`Asset is not a file: ${relativeAssetPath}`);
      }

      if (path.extname(resolvedAssetPath).toLowerCase() !== PNG_EXTENSION) {
        throw new Error(
          `State asset must be a PNG sprite strip: ${relativeAssetPath}`,
        );
      }
      const size = await readPngSize(resolvedAssetPath);
      if (size.width !== manifest.renderWidthPx * stateConfig.frameCount) {
        throw new Error(
          `State sprite width must equal renderWidthPx * frameCount: ${relativeAssetPath}`,
        );
      }
      if (size.height !== manifest.renderHeightPx) {
        throw new Error(
          `State sprite height must equal renderHeightPx: ${relativeAssetPath}`,
        );
      }
    }),
  );

  if (validateOnly) {
    process.stdout.write(
      JSON.stringify(
        {
          packId: manifest.id,
          name: manifest.name,
          revision: manifest.revision ?? 1,
          draftPath: resolvedSourceDir,
          valid: true,
        },
        null,
        2,
      ),
    );
    return;
  }

  const codexHome = process.env.CODEX_HOME ?? path.join(os.homedir(), ".codex");
  const destinationRoot = path.join(codexHome, "pets", "packs");
  const destinationDir = path.join(destinationRoot, manifest.id);

  await fs.mkdir(destinationRoot, { recursive: true });
  await fs.rm(destinationDir, { recursive: true, force: true });
  await fs.cp(resolvedSourceDir, destinationDir, { recursive: true });

  process.stdout.write(
    JSON.stringify(
      {
        packId: manifest.id,
        name: manifest.name,
        revision: manifest.revision ?? 1,
        installedPath: destinationDir,
      },
      null,
      2,
    ),
  );
}

async function readManifest(sourceDir) {
  const manifestPath = path.join(sourceDir, "manifest.json");
  const raw = await fs.readFile(manifestPath, "utf8");
  return JSON.parse(raw);
}

function validateManifest(manifest) {
  if (manifest?.schemaVersion !== 1) {
    throw new Error("manifest.json must set schemaVersion to 1");
  }
  if (typeof manifest.id !== "string" || !PACK_ID_PATTERN.test(manifest.id)) {
    throw new Error("manifest.json id must be lowercase kebab-case");
  }
  if (typeof manifest.name !== "string" || manifest.name.trim() === "") {
    throw new Error("manifest.json name is required");
  }
  if (
    manifest.revision != null &&
    (typeof manifest.revision !== "number" ||
      !Number.isInteger(manifest.revision) ||
      manifest.revision < 1)
  ) {
    throw new Error("manifest.json revision must be a positive integer");
  }
  const hasRenderDimensions =
    typeof manifest.renderWidthPx === "number" &&
    Number.isInteger(manifest.renderWidthPx) &&
    manifest.renderWidthPx > 0 &&
    typeof manifest.renderHeightPx === "number" &&
    Number.isInteger(manifest.renderHeightPx) &&
    manifest.renderHeightPx > 0;
  if (!hasRenderDimensions) {
    throw new Error(
      "manifest.json must set positive integer renderWidthPx and renderHeightPx",
    );
  }
  if (
    typeof manifest.thumbnail !== "string" ||
    manifest.thumbnail.trim() === ""
  ) {
    throw new Error("manifest.json thumbnail is required");
  }
  if (typeof manifest.states !== "object" || manifest.states == null) {
    throw new Error("manifest.json states is required");
  }
  for (const state of REQUIRED_STATES) {
    const stateConfig = manifest.states[state];
    if (typeof stateConfig?.path !== "string") {
      throw new Error(`manifest.json states.${state}.path is required`);
    }
    if (
      typeof stateConfig.frameCount !== "number" ||
      !Number.isInteger(stateConfig.frameCount) ||
      stateConfig.frameCount < 2
    ) {
      throw new Error(
        `manifest.json states.${state}.frameCount must be an integer greater than 1`,
      );
    }
    if (
      typeof stateConfig.frameDurationMs !== "number" ||
      !Number.isInteger(stateConfig.frameDurationMs) ||
      stateConfig.frameDurationMs < 1
    ) {
      throw new Error(
        `manifest.json states.${state}.frameDurationMs must be a positive integer`,
      );
    }
  }
}

function resolvePackPath(packRoot, relativeAssetPath) {
  const resolvedPath = path.resolve(packRoot, relativeAssetPath);
  const relativeFromPack = path.relative(packRoot, resolvedPath);
  if (
    relativeFromPack === "" ||
    relativeFromPack.startsWith("..") ||
    path.isAbsolute(relativeFromPack)
  ) {
    throw new Error(`Asset path escapes pack root: ${relativeAssetPath}`);
  }
  return resolvedPath;
}

async function readPngSize(assetPath) {
  const handle = await fs.open(assetPath, "r");
  try {
    const header = Buffer.alloc(24);
    await handle.read(header, 0, header.length, 0);
    if (!header.subarray(0, PNG_SIGNATURE.length).equals(PNG_SIGNATURE)) {
      throw new Error(`Asset is not a PNG file: ${assetPath}`);
    }
    return {
      width: header.readUInt32BE(16),
      height: header.readUInt32BE(20),
    };
  } finally {
    await handle.close();
  }
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
});
