import hre from "hardhat";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function updateEnv(filePath: string, key: string, value: string) {
  if (!fs.existsSync(filePath)) {
    console.warn(`⚠️  Env file not found: ${filePath}`);
    return;
  }
  let contents = fs.readFileSync(filePath, "utf8");
  const regex = new RegExp(`^${key}=.*$`, "m");
  if (regex.test(contents)) {
    contents = contents.replace(regex, `${key}=${value}`);
  } else {
    contents += `\n${key}=${value}`;
  }
  fs.writeFileSync(filePath, contents, "utf8");
  console.log(`✅ Updated ${key} in ${path.basename(filePath)}`);
}

async function main() {
  const { ethers } = await hre.network.connect();
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with:", deployer.address);

  const Voting = await ethers.getContractFactory("SecureVoting");
  const candidates = ["Alice", "Bob", "Charlie"];
  const contract = await Voting.deploy(deployer.address, candidates);
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("Contract deployed at:", address);

  // Auto-update env files
  const root = path.resolve(__dirname, "../..");
  updateEnv(path.join(root, "backend", ".env"),          "CONTRACT_ADDRESS",              address);
  updateEnv(path.join(root, "frontend", ".env.local"),   "NEXT_PUBLIC_CONTRACT_ADDRESS",  address);

  console.log("\n🎉 Done! Restart backend (npm start) and frontend (npm run dev) to pick up the new address.");
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});