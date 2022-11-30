module Main where

import qualified Data.ByteString      as S
import qualified Data.ByteString.Lazy as B
import           Data.List            (foldl', insertBy, sortBy)
import qualified Data.Map             as M
import           Data.Ord             (comparing)
import           Huffman

main :: IO ()
main = do
  testFile1 <- readFile "resources/test1.txt"
  testFile2 <- readFile "resources/test2.txt"
  testFile3 <- readFile "resources/test3.txt"
  let testText = lines testFile1 ++ lines testFile2 ++ lines testFile3
  let frequencies = histogram (concat testText)
  let sortedFrequencies = sortBy (comparing swap) frequencies
  putStrLn "\nСимволи та їх частота:\n"
  mapM_ print sortedFrequencies
  let huffmanTree = sortedHuffman sortedFrequencies
  putStrLn "\nДерево Хоффмана:\n"
  print huffmanTree
  putStrLn "\nРезультат:\n"
  let encoding = codes huffmanTree
  let showCode (s, bits) = show s ++ " -> " ++ showBits bits
  mapM_ (putStrLn . showCode) (M.toList encoding)
  putStrLn "\nЗакодований текст:\n"
  let encoded = map (encode encoding) testText
  mapM_ (print . showBits) encoded
  let encBits0 = padToEight (concat encoded)
  let bits = bitpack encBits0
  B.writeFile "result.bin" bits
  let Right encBits1 = bitunpack . S.pack . B.unpack $ bits
  putStrLn "\nРозкодований текст:\n"
  let decoded = map (decode huffmanTree) encoded
  mapM_ print decoded
